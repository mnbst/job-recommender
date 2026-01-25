"""Pytest fixtures for job-recommender tests."""

import pytest

from app.services.models import (
    DeveloperProfile,
    FileContent,
    JobFit,
    NotableProject,
    RepoInfo,
    SkillAssessment,
    TechStack,
)


@pytest.fixture
def sample_repos() -> list[RepoInfo]:
    """Sample repository data for testing."""
    return [
        RepoInfo(
            name="web-app",
            description="A modern web application",
            language="TypeScript",
            languages={"TypeScript": 5000, "Python": 2000, "CSS": 1000},
            topics=["react", "nextjs", "tailwind"],
            readme="# Web App\nA modern web application built with Next.js",
            stars=50,
            forks=10,
            updated_at="2024-01-15T10:00:00Z",
            is_fork=False,
            file_structure=["src", "src/App.tsx", "package.json", "tsconfig.json"],
            dependency_files=[
                FileContent(
                    path="package.json",
                    content='{"dependencies": {"react": "^18.0.0", "next": "^14.0.0"}}',
                )
            ],
            main_files=[
                FileContent(
                    path="src/App.tsx",
                    content="export default function App() { return <div>Hello</div> }",
                )
            ],
            config_files=["tsconfig.json"],
        ),
        RepoInfo(
            name="api-server",
            description="REST API server",
            language="Python",
            languages={"Python": 8000, "Dockerfile": 200},
            topics=["fastapi", "python", "rest-api"],
            readme="# API Server\nFastAPI-based REST API server",
            stars=30,
            forks=5,
            updated_at="2024-01-10T10:00:00Z",
            is_fork=False,
            file_structure=["app.py", "requirements.txt", "Dockerfile"],
            dependency_files=[
                FileContent(
                    path="requirements.txt",
                    content="fastapi==0.100.0\nuvicorn==0.23.0",
                )
            ],
            main_files=[
                FileContent(
                    path="app.py",
                    content="from fastapi import FastAPI\napp = FastAPI()",
                )
            ],
            config_files=["Dockerfile"],
        ),
    ]


@pytest.fixture
def sample_profile() -> DeveloperProfile:
    """Sample developer profile for testing."""
    return DeveloperProfile(
        tech_stack=TechStack(
            languages=["Python", "TypeScript", "Go"],
            frameworks=["FastAPI", "React", "Next.js"],
            infrastructure=["Docker", "Kubernetes", "GCP"],
        ),
        expertise_areas=["バックエンド開発", "API設計", "クラウドインフラ"],
        skill_assessment=SkillAssessment(
            code_quality="高品質なコードを書く能力がある",
            design_ability="スケーラブルな設計ができる",
            completion_rate="プロジェクトを完遂する力がある",
        ),
        notable_projects=[
            NotableProject(
                name="web-app", highlight="モダンなフロントエンド技術の活用"
            ),
            NotableProject(name="api-server", highlight="本格的なAPI設計"),
        ],
        interests=["クラウドネイティブ", "マイクロサービス", "DevOps"],
        job_fit=JobFit(
            ideal_roles=["バックエンドエンジニア", "フルスタックエンジニア"],
            company_types=["テックスタートアップ", "SaaS企業"],
            keywords=["Python", "FastAPI", "クラウド"],
        ),
        summary="バックエンドとインフラに強みを持つフルスタックエンジニア。",
    )


@pytest.fixture
def sample_profile_dict(sample_profile: DeveloperProfile) -> dict:
    """Sample developer profile as dict for testing."""
    return sample_profile.model_dump()
