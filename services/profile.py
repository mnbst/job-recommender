"""Profile generation using LLM (Vertex AI)."""

import json
import os

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


def analyze_job_matches(profile: dict, jobs: list) -> list[dict]:
    """Analyze how well each job matches the developer profile.

    Args:
        profile: Developer profile from generate_profile()
        jobs: List of JobResult from search_jobs()

    Returns:
        List of job analyses with match scores and reasons
    """
    if not jobs:
        return []

    init_vertex_ai()
    model = GenerativeModel("gemini-1.5-flash")

    # Prepare job summaries
    job_summaries = []
    for i, job in enumerate(jobs):
        job_summaries.append(
            {
                "index": i,
                "title": job.title,
                "company": job.company_name,
                "location": job.location,
                "description": job.description[:500],
                "extensions": job.detected_extensions,
            }
        )

    prompt = f"""あなたは技術者採用のマッチングエキスパートです。
以下の開発者プロファイルと求人リストを比較し、各求人のマッチ度を分析してください。

## 開発者プロファイル
{json.dumps(profile, ensure_ascii=False, indent=2)}

## 求人リスト
{json.dumps(job_summaries, ensure_ascii=False, indent=2)}

各求人について以下を評価してください:
1. マッチ度 (1-5): 技術スタック、経験、興味との適合度
2. マッチ理由: なぜこの求人が合う/合わないか（1-2文）
3. 注目ポイント: この求人の魅力的な点

以下のJSON配列形式で回答してください:
[
    {{
        "index": 0,
        "match_score": 4,
        "match_reason": "マッチ理由",
        "highlights": ["注目ポイント1", "注目ポイント2"]
    }}
]

マッチ度が高い順にソートして返してください。
"""

    response = model.generate_content(prompt)

    response_text = response.text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]

    return json.loads(response_text)
