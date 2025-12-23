"""Profile generation using LLM (Vertex AI)."""

import json
import os

import vertexai
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from vertexai.generative_models import GenerativeModel

from services.github import RepoInfo


class TechStack(BaseModel):
    """技術スタック情報."""

    languages: list[str] = Field(description="プログラミング言語リスト")
    frameworks: list[str] = Field(description="フレームワークリスト")
    infrastructure: list[str] = Field(description="インフラ技術リスト")


class SkillAssessment(BaseModel):
    """スキル評価."""

    code_quality: str = Field(description="コード品質の評価コメント")
    design_ability: str = Field(description="設計力の評価コメント")
    completion_rate: str = Field(description="完遂力の評価コメント")


class NotableProject(BaseModel):
    """特筆すべきプロジェクト."""

    name: str = Field(description="プロジェクト名")
    highlight: str = Field(description="特筆点")


class JobFit(BaseModel):
    """マッチする求人の特徴."""

    ideal_roles: list[str] = Field(description="マッチする職種リスト")
    company_types: list[str] = Field(description="マッチする企業タイプ")
    keywords: list[str] = Field(description="求人検索キーワード")


class DeveloperProfile(BaseModel):
    """開発者プロファイル."""

    tech_stack: TechStack = Field(description="技術スタック")
    expertise_areas: list[str] = Field(description="得意領域リスト")
    skill_assessment: SkillAssessment = Field(description="スキル評価")
    notable_projects: list[NotableProject] = Field(description="特筆すべきプロジェクト")
    interests: list[str] = Field(description="興味・関心領域リスト")
    job_fit: JobFit = Field(description="マッチする求人の特徴")
    summary: str = Field(description="総合評価（2-3文）")


def init_vertex_ai():
    """Initialize Vertex AI with project settings."""
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("GCP_LOCATION", "asia-northeast1")
    vertexai.init(project=project_id, location=location)


def generate_profile(repos: list[RepoInfo]) -> dict:
    """Generate a developer profile from GitHub repositories using LLM.

    Analyzes repositories from a recruiter's perspective.
    """
    init_vertex_ai()
    model = GenerativeModel("gemini-2.5-flash")
    parser = PydanticOutputParser(pydantic_object=DeveloperProfile)

    # Prepare repository summaries
    repo_summaries = []
    for repo in repos:
        # フォークは除外（オリジナル作品を重視）
        if repo.is_fork:
            continue

        summary = {
            "name": repo.name,
            "description": repo.description,
            "main_language": repo.language,
            "languages": repo.languages,
            "topics": repo.topics,
            "stars": repo.stars,
            "readme_preview": repo.readme[:2000] if repo.readme else None,
            "file_structure": repo.file_structure[:50],  # 最大50ファイル
            "config_files": repo.config_files,
            "dependencies": [
                {"path": f.path, "content": f.content[:1000]}
                for f in repo.dependency_files
            ],
            "code_samples": [
                {"path": f.path, "content": f.content[:1500]}
                for f in repo.main_files
            ],
        }
        repo_summaries.append(summary)

    prompt = f"""あなたは技術採用担当者です。以下のGitHubリポジトリ情報を分析し、
この開発者のプロファイルを生成してください。

提供される情報：
- リポジトリ基本情報（名前、説明、言語、トピック、スター数）
- ファイル構造（プロジェクトの構成）
- 設定ファイル（Dockerfile、CI/CD、Terraform等）
- 依存関係（package.json、requirements.txt等の内容）
- コードサンプル（主要ファイルの実装内容）

採用担当者として以下の観点で評価してください：
1. 技術スタック（言語、フレームワーク、インフラ）- 依存関係から具体的なライブラリを特定
2. 得意領域（フロントエンド、バックエンド、インフラ、データ等）
3. 技術力の印象（コード品質、設計力、完遂力）- コードサンプルから判断
4. 特筆すべきプロジェクト
5. 推定される興味・関心領域
6. マッチしそうな求人の特徴

リポジトリ情報:
{json.dumps(repo_summaries, ensure_ascii=False, indent=2)}

{parser.get_format_instructions()}
"""

    response = model.generate_content(prompt)
    profile = parser.parse(response.text)

    return profile.model_dump()
