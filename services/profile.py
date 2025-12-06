"""Profile generation using LLM (Vertex AI)."""

import os
import json

import vertexai
from vertexai.generative_models import GenerativeModel

from services.github import RepoInfo


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
    model = GenerativeModel("gemini-1.5-flash")

    # Prepare repository summaries
    repo_summaries = []
    for repo in repos:
        summary = {
            "name": repo.name,
            "description": repo.description,
            "main_language": repo.language,
            "languages": repo.languages,
            "topics": repo.topics,
            "stars": repo.stars,
            "readme_preview": repo.readme[:2000] if repo.readme else None,
        }
        repo_summaries.append(summary)

    prompt = f"""あなたは技術採用担当者です。以下のGitHubリポジトリ情報を分析し、
この開発者のプロファイルを生成してください。

採用担当者として以下の観点で評価してください：
1. 技術スタック（言語、フレームワーク、インフラ）
2. 得意領域（フロントエンド、バックエンド、インフラ、データ等）
3. 技術力の印象（コード品質、設計力、完遂力）
4. 特筆すべきプロジェクト
5. 推定される興味・関心領域
6. マッチしそうな求人の特徴

リポジトリ情報:
{json.dumps(repo_summaries, ensure_ascii=False, indent=2)}

以下のJSON形式で回答してください：
{{
    "tech_stack": {{
        "languages": ["言語リスト"],
        "frameworks": ["フレームワークリスト"],
        "infrastructure": ["インフラ技術リスト"]
    }},
    "expertise_areas": ["得意領域リスト"],
    "skill_assessment": {{
        "code_quality": "評価コメント",
        "design_ability": "評価コメント",
        "completion_rate": "評価コメント"
    }},
    "notable_projects": [
        {{"name": "プロジェクト名", "highlight": "特筆点"}}
    ],
    "interests": ["興味・関心領域リスト"],
    "job_fit": {{
        "ideal_roles": ["マッチする職種リスト"],
        "company_types": ["マッチする企業タイプ"],
        "keywords": ["求人検索キーワード"]
    }},
    "summary": "総合評価（2-3文）"
}}
"""

    response = model.generate_content(prompt)

    # Parse JSON from response
    response_text = response.text.strip()
    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    return json.loads(response_text)
