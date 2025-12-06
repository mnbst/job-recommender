"""GitHub API integration for repository analysis."""

import os
from dataclasses import dataclass

from github import Github
from github.Repository import Repository


@dataclass
class RepoInfo:
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
    )


def analyze_github_profile(username: str, repo_limit: int = 10) -> list[RepoInfo]:
    """Analyze a GitHub user's profile and return repository information."""
    repos = get_user_repos(username, limit=repo_limit)
    return [extract_repo_info(repo) for repo in repos]
