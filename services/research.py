"""Job search using Perplexity API with built-in matching analysis."""

import json
import logging
import os
from dataclasses import dataclass

from perplexity import Perplexity

logger = logging.getLogger(__name__)


@dataclass
class JobSource:
    """Source URL for job information."""

    url: str
    used_for: str


@dataclass
class MatchReason:
    """Explanation for why a job is a good match."""

    summary: str
    matched_conditions: list[str]
    why_good: str


@dataclass
class JobRecommendation:
    """Job recommendation from Perplexity API."""

    job_title: str
    company: str
    location: str
    salary_range: str | None
    reason: MatchReason
    sources: list[JobSource]


@dataclass
class JobSearchResult:
    """Result from Perplexity job search."""

    recommendations: list[JobRecommendation]
    status: str
    error: str | None = None


@dataclass
class JobPreferences:
    """求職者の希望条件."""

    location: str = "東京"
    salary_range: str = "指定なし"
    work_style: list[str] | None = None
    job_type: list[str] | None = None
    other: str = ""


def build_search_prompt(profile: dict, preferences: JobPreferences) -> str:
    """Build Perplexity search prompt from developer profile."""
    tech_stack = profile.get("tech_stack", {})
    job_fit = profile.get("job_fit", {})

    roles = job_fit.get("ideal_roles", [])[:3]
    languages = tech_stack.get("languages", [])[:3]
    frameworks = tech_stack.get("frameworks", [])[:3]

    skills = languages + frameworks

    # 希望条件を構築
    conditions = [f"勤務地: {preferences.location}"]
    if preferences.salary_range != "指定なし":
        conditions.append(f"希望年収: {preferences.salary_range}")
    if preferences.work_style:
        conditions.append(f"働き方: {', '.join(preferences.work_style)}")
    if preferences.job_type:
        conditions.append(f"希望職種: {', '.join(preferences.job_type)}")
    if preferences.other:
        conditions.append(f"その他: {preferences.other}")

    conditions_text = "\n- ".join(conditions)

    return f"""You are a job search assistant.

Search the web and find up to 3 job postings that match the following criteria:
- Role: {", ".join(roles) if roles else "Software Engineer"}
- Skills: {", ".join(skills) if skills else "any"}
- {conditions_text}

For each recommended job:
- Explain WHY it is a good match for the user
- Clearly state which criteria are satisfied
- Provide the explanation in Japanese
- Provide the original job posting URL as evidence

Return the result strictly in the following JSON format:
{{
  "recommendations": [
    {{
      "job_title": "Senior Data Engineer",
      "company": "ABC Tech",
      "location": "Tokyo",
      "salary_range": "10M-14M JPY",
      "reason": {{
        "summary": "GCPを中心とした大規模データ基盤の構築経験が活かせる求人です。",
        "matched_conditions": ["勤務地が東京", "年収1000万円以上"],
        "why_good": "ユーザーがこれまで取り組んできたGCP基盤設計やETL構築の経験と、求人要件が非常によく一致しています。"
      }},
      "sources": [
        {{"url": "https://careers.example.com/jobs/123", "used_for": "salary, required skills, location"}}
      ]
    }}
  ]
}}
"""


def search_jobs(
    profile: dict, preferences: JobPreferences | None = None
) -> JobSearchResult:
    """Search for jobs using Perplexity API with built-in matching analysis.

    Args:
        profile: Developer profile from generate_profile()
        preferences: 求職者の希望条件

    Returns:
        JobSearchResult with recommendations and status
    """
    if preferences is None:
        preferences = JobPreferences()

    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return JobSearchResult(
            recommendations=[],
            status="error",
            error="PERPLEXITY_API_KEY environment variable is required",
        )

    prompt = build_search_prompt(profile, preferences)

    # 検索条件をログ出力
    tech_stack = profile.get("tech_stack", {})
    job_fit = profile.get("job_fit", {})
    roles = job_fit.get("ideal_roles", [])[:3]
    skills = tech_stack.get("languages", [])[:3] + tech_stack.get("frameworks", [])[:3]

    search_params = {
        "role": roles if roles else ["Software Engineer"],
        "skills": skills if skills else [],
        "location": preferences.location,
        "salary_range": preferences.salary_range,
        "work_style": preferences.work_style or [],
        "job_type": preferences.job_type or [],
        "other": preferences.other,
    }

    # Cloud Run環境では構造化ログ、ローカルでは整形して出力
    if os.environ.get("K_SERVICE"):
        logger.info(
            "求人検索開始", extra={"json_fields": {"search_params": search_params}}
        )
    else:
        logger.info(f"求人検索開始: {json.dumps(search_params, ensure_ascii=False)}")

    try:
        client = Perplexity()

        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": prompt}],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "recommendations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "job_title": {"type": "string"},
                                        "company": {"type": "string"},
                                        "location": {"type": "string"},
                                        "salary_range": {"type": "string"},
                                        "reason": {
                                            "type": "object",
                                            "properties": {
                                                "summary": {"type": "string"},
                                                "matched_conditions": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                },
                                                "why_good": {"type": "string"},
                                            },
                                            "required": [
                                                "summary",
                                                "matched_conditions",
                                                "why_good",
                                            ],
                                        },
                                        "sources": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "url": {"type": "string"},
                                                    "used_for": {"type": "string"},
                                                },
                                                "required": ["url", "used_for"],
                                            },
                                        },
                                    },
                                    "required": [
                                        "job_title",
                                        "company",
                                        "location",
                                        "reason",
                                        "sources",
                                    ],
                                },
                            }
                        },
                        "required": ["recommendations"],
                    }
                },
            },
        )

        content = completion.choices[0].message.content
        if not isinstance(content, str):
            return JobSearchResult(
                recommendations=[],
                status="error",
                error="Unexpected response format from Perplexity API",
            )

        result_json = json.loads(content)

        recommendations = []
        for rec in result_json.get("recommendations", []):
            reason_data = rec.get("reason", {})
            recommendations.append(
                JobRecommendation(
                    job_title=rec.get("job_title", ""),
                    company=rec.get("company", ""),
                    location=rec.get("location", ""),
                    salary_range=rec.get("salary_range"),
                    reason=MatchReason(
                        summary=reason_data.get("summary", ""),
                        matched_conditions=reason_data.get("matched_conditions", []),
                        why_good=reason_data.get("why_good", ""),
                    ),
                    sources=[
                        JobSource(url=s.get("url", ""), used_for=s.get("used_for", ""))
                        for s in rec.get("sources", [])
                    ],
                )
            )

        return JobSearchResult(recommendations=recommendations, status="success")

    except Exception as e:
        return JobSearchResult(
            recommendations=[],
            status="error",
            error=str(e),
        )
