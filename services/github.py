"""GitHub API integration for repository analysis."""

import logging
import os

from github import Github
from github.ContentFile import ContentFile
from github.GithubException import GithubException, UnknownObjectException
from github.Repository import Repository

from services.logging_config import log_structured
from services.models import FileContent, RepoInfo, RepoMetadata

logger = logging.getLogger(__name__)

# 依存ファイルのパターン
DEPENDENCY_FILES = [
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "pom.xml",
    "build.gradle",
    "composer.json",
]

# 主要コードファイルのパターン
MAIN_FILE_PATTERNS = [
    "main.py",
    "app.py",
    "index.py",
    "index.js",
    "index.ts",
    "main.js",
    "main.ts",
    "main.go",
    "main.rs",
    "App.jsx",
    "App.tsx",
    "server.py",
    "server.js",
]

# 設定ファイルのパターン
CONFIG_FILES = [
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".github/workflows",
    "terraform",
    "Makefile",
    "tsconfig.json",
    "webpack.config.js",
    "vite.config.ts",
]


def get_github_client() -> Github:
    """Create GitHub client with token from environment."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return Github(token)


def get_user_repos(username: str, limit: int = 10) -> list[Repository]:
    """Fetch user's public repositories sorted by recent activity."""
    client = get_github_client()
    user = client.get_user(username)
    repos = list(user.get_repos(sort="updated", direction="desc"))
    return repos[:limit]


def get_repos_metadata(username: str, limit: int = 30) -> list[RepoMetadata]:
    """Fetch lightweight metadata for user's repositories.

    Args:
        username: GitHub username
        limit: Maximum number of repos to fetch (default: 30)

    Returns:
        List of RepoMetadata for selection UI
    """
    repos = get_user_repos(username, limit)
    return [
        RepoMetadata(
            name=repo.name,
            full_name=repo.full_name,
            description=repo.description,
            language=repo.language,
            stars=repo.stargazers_count,
            is_fork=repo.fork,
        )
        for repo in repos
    ]


def get_repos_by_names(username: str, repo_names: list[str]) -> list[Repository]:
    """Fetch specific repositories by name.

    Args:
        username: GitHub username
        repo_names: List of repository names to fetch

    Returns:
        List of Repository objects
    """
    client = get_github_client()
    repos = []
    for name in repo_names:
        try:
            repo = client.get_repo(f"{username}/{name}")
            repos.append(repo)
        except Exception:
            log_structured(
                logger,
                "Failed to fetch repo",
                level=logging.ERROR,
                exc_info=True,
                username=username,
                repo=name,
            )
    return repos


def get_repo_structure(repo: Repository, max_depth: int = 2) -> list[str]:
    """Get repository file/directory structure up to max_depth.

    Args:
        repo: GitHub repository object
        max_depth: Maximum directory depth to traverse (default: 2)

    Returns:
        List of file/directory paths
    """
    files: list[str] = []
    try:
        contents = repo.get_contents("")
        if isinstance(contents, list):
            queue: list[tuple[ContentFile, int]] = [(item, 0) for item in contents]
        else:
            queue = [(contents, 0)]

        while queue:
            item, depth = queue.pop(0)
            files.append(item.path)

            if item.type == "dir" and depth < max_depth:
                try:
                    sub_contents = repo.get_contents(item.path)
                    if isinstance(sub_contents, list):
                        queue.extend((sub, depth + 1) for sub in sub_contents)
                except Exception:
                    log_structured(
                        logger,
                        "Failed to read directory",
                        level=logging.ERROR,
                        exc_info=True,
                        path=item.path,
                    )
    except Exception:
        log_structured(
            logger,
            "Failed to get repo structure",
            level=logging.ERROR,
            exc_info=True,
            repo=repo.full_name,
        )

    return files


def get_file_content(repo: Repository, path: str) -> str | None:
    """Get content of a specific file.

    Args:
        repo: GitHub repository object
        path: File path in the repository

    Returns:
        File content as string, or None if not found
    """
    try:
        file = repo.get_contents(path)
        if isinstance(file, ContentFile):
            return file.decoded_content.decode("utf-8")
    except Exception:
        log_structured(
            logger,
            "Failed to read file",
            level=logging.ERROR,
            exc_info=True,
            path=path,
        )
    return None


def get_dependency_files(repo: Repository, structure: list[str]) -> list[FileContent]:
    """Get dependency files from repository.

    Args:
        repo: GitHub repository object
        structure: List of file paths in the repository

    Returns:
        List of FileContent with dependency file contents
    """
    return _collect_file_contents(
        repo,
        structure,
        DEPENDENCY_FILES,
        content_limit=5000,
    )


def get_main_files(repo: Repository, structure: list[str]) -> list[FileContent]:
    """Get main code files from repository.

    Args:
        repo: GitHub repository object
        structure: List of file paths in the repository

    Returns:
        List of FileContent with main file contents
    """
    # src/やapp/ディレクトリ内も検索
    search_paths = [""] + [
        f"{d}/"
        for d in ["src", "app", "lib", "cmd"]
        if any(p.startswith(d + "/") for p in structure)
    ]
    return _collect_file_contents(
        repo,
        structure,
        MAIN_FILE_PATTERNS,
        search_paths=search_paths,
        content_limit=3000,
        max_files=3,
    )


def get_config_files(structure: list[str]) -> list[str]:
    """Identify config files present in the repository.

    Args:
        structure: List of file paths in the repository

    Returns:
        List of config file paths found
    """
    found: list[str] = []

    for config in CONFIG_FILES:
        for path in structure:
            if path == config or path.startswith(config + "/"):
                found.append(path)
                break

    return found


def _collect_file_contents(
    repo: Repository,
    structure: list[str],
    patterns: list[str],
    *,
    search_paths: list[str] | None = None,
    content_limit: int = 5000,
    max_files: int | None = None,
) -> list[FileContent]:
    """ファイルパターンに一致する内容を収集."""
    results: list[FileContent] = []
    prefixes = search_paths or [""]

    for pattern in patterns:
        for prefix in prefixes:
            path = f"{prefix}{pattern}"
            if path in structure or pattern in structure:
                actual_path = path if path in structure else pattern
                content = get_file_content(repo, actual_path)
                if content:
                    # 長すぎる場合は切り詰め
                    results.append(
                        FileContent(path=actual_path, content=content[:content_limit])
                    )
                    break

        if max_files is not None and len(results) >= max_files:
            break

    return results


def extract_repo_info(repo: Repository) -> RepoInfo:
    """Extract relevant information from a repository."""
    # Get README content
    readme = None
    try:
        readme_file = repo.get_readme()
        readme = readme_file.decoded_content.decode("utf-8")
    except UnknownObjectException:
        log_structured(
            logger,
            "README not found",
            level=logging.INFO,
            repo=repo.full_name,
        )
    except GithubException:
        log_structured(
            logger,
            "Failed to read README",
            level=logging.ERROR,
            exc_info=True,
            repo=repo.full_name,
        )
    except Exception:
        log_structured(
            logger,
            "Failed to read README",
            level=logging.ERROR,
            exc_info=True,
            repo=repo.full_name,
        )

    # Get languages
    languages = dict(repo.get_languages())

    # Get file structure
    structure = get_repo_structure(repo)

    # Get dependency files
    dependency_files = get_dependency_files(repo, structure)

    # Get main files
    main_files = get_main_files(repo, structure)

    # Get config files
    config_files = get_config_files(structure)

    return RepoInfo(
        name=repo.name,
        description=repo.description,
        language=repo.language,
        languages=languages,
        topics=repo.get_topics(),
        readme=readme,
        stars=repo.stargazers_count,
        forks=repo.forks_count,
        updated_at=repo.updated_at.isoformat() if repo.updated_at else "",
        is_fork=repo.fork,
        file_structure=structure,
        dependency_files=dependency_files,
        main_files=main_files,
        config_files=config_files,
    )


def analyze_github_profile(username: str, repo_limit: int = 10) -> list[RepoInfo]:
    """Analyze a GitHub user's profile and return repository information."""
    repos = get_user_repos(username, limit=repo_limit)
    return [extract_repo_info(repo) for repo in repos]


def analyze_selected_repos(username: str, repo_names: list[str]) -> list[RepoInfo]:
    """Analyze selected repositories and return repository information.

    Args:
        username: GitHub username
        repo_names: List of repository names to analyze

    Returns:
        List of RepoInfo for selected repositories
    """
    repos = get_repos_by_names(username, repo_names)
    return [extract_repo_info(repo) for repo in repos]
