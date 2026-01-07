"""GitHub API integration for repository analysis."""

import os

from github import Github
from github.ContentFile import ContentFile
from github.Repository import Repository
from pydantic import BaseModel, Field

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


class FileContent(BaseModel):
    """File content from repository."""

    path: str
    content: str


class RepoInfo(BaseModel):
    """Repository information extracted from GitHub."""

    name: str
    description: str | None
    language: str | None
    languages: dict[str, int]
    topics: list[str]
    readme: str | None
    stars: int
    forks: int
    updated_at: str
    is_fork: bool = False
    file_structure: list[str] = Field(default_factory=list)
    dependency_files: list[FileContent] = Field(default_factory=list)
    main_files: list[FileContent] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)


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
                    pass
    except Exception:
        pass

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
        pass
    return None


def get_dependency_files(repo: Repository, structure: list[str]) -> list[FileContent]:
    """Get dependency files from repository.

    Args:
        repo: GitHub repository object
        structure: List of file paths in the repository

    Returns:
        List of FileContent with dependency file contents
    """
    results: list[FileContent] = []

    for dep_file in DEPENDENCY_FILES:
        if dep_file in structure:
            content = get_file_content(repo, dep_file)
            if content:
                # 長すぎる場合は切り詰め
                results.append(FileContent(path=dep_file, content=content[:5000]))

    return results


def get_main_files(repo: Repository, structure: list[str]) -> list[FileContent]:
    """Get main code files from repository.

    Args:
        repo: GitHub repository object
        structure: List of file paths in the repository

    Returns:
        List of FileContent with main file contents
    """
    results: list[FileContent] = []

    # src/やapp/ディレクトリ内も検索
    search_paths = [""] + [
        f"{d}/"
        for d in ["src", "app", "lib", "cmd"]
        if any(p.startswith(d + "/") for p in structure)
    ]

    for main_file in MAIN_FILE_PATTERNS:
        for prefix in search_paths:
            path = f"{prefix}{main_file}"
            if path in structure or main_file in structure:
                actual_path = path if path in structure else main_file
                content = get_file_content(repo, actual_path)
                if content:
                    # 長すぎる場合は切り詰め
                    results.append(
                        FileContent(path=actual_path, content=content[:3000])
                    )
                    break

    return results[:3]  # 最大3ファイル


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


def extract_repo_info(repo: Repository) -> RepoInfo:
    """Extract relevant information from a repository."""
    # Get README content
    readme = None
    try:
        readme_file = repo.get_readme()
        readme = readme_file.decoded_content.decode("utf-8")
    except Exception:
        pass

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
