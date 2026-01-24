"""Job search using Perplexity API with built-in matching analysis."""

import json
import logging
import os

from perplexity import Perplexity

from services.logging_config import log_structured
from services.models import (
    JobPreferences,
    JobRecommendation,
    JobSearchResult,
    JobSource,
    JobUrlResult,
    MatchReason,
)

logger = logging.getLogger(__name__)


def build_search_prompt(
    profile: dict,
    preferences: JobPreferences,
    exclude_companies: list[str] | None = None,
) -> str:
    """Build Perplexity search prompt from developer profile."""
    tech_stack = profile.get("tech_stack", {})
    job_fit = profile.get("job_fit", {})
    skill_assessment = profile.get("skill_assessment", {})
    interests = profile.get("interests", [])[:5]

    roles = job_fit.get("ideal_roles", [])[:3]
    languages = tech_stack.get("languages", [])[:3]
    frameworks = tech_stack.get("frameworks", [])[:3]
    infrastructure = tech_stack.get("infrastructure", [])[:3]
    keywords = job_fit.get("keywords", [])[:5]

    skills = languages + frameworks + infrastructure

    # スキル評価の要約を構築
    expertise_summary = []
    if skill_assessment.get("code_quality"):
        expertise_summary.append(
            f"コード品質: {skill_assessment['code_quality'][:100]}"
        )
    if skill_assessment.get("design_ability"):
        expertise_summary.append(f"設計力: {skill_assessment['design_ability'][:100]}")

    # 希望条件を構築
    conditions = [f"勤務地: {preferences.location}"]
    if preferences.salary_range != "指定なし":
        conditions.append(f"希望年収: {preferences.salary_range}")
    if preferences.work_style:
        conditions.append(f"働き方: {', '.join(preferences.work_style)}")
    if preferences.job_type:
        conditions.append(f"希望職種: {', '.join(preferences.job_type)}")
    if preferences.employment_type:
        conditions.append(f"雇用形態: {', '.join(preferences.employment_type)}")
    if preferences.other:
        conditions.append(f"その他の希望・アピールポイント: {preferences.other}")

    conditions_text = "\n- ".join(conditions)
    keywords_text = ", ".join(keywords) if keywords else ""
    interests_text = ", ".join(interests) if interests else ""
    expertise_text = "\n".join(expertise_summary) if expertise_summary else ""

    # 除外企業リスト
    exclude_text = ""
    if exclude_companies:
        exclude_text = f"\n\nIMPORTANT: Do NOT include jobs from these companies (already shown): {', '.join(exclude_companies)}"

    return f"""You are a job search assistant.{exclude_text}

Search the web and find EXACTLY 3 job postings that match the following criteria.
IMPORTANT: You MUST return exactly 3 recommendations. Do not return fewer than 3.
- Role: {", ".join(roles) if roles else "Software Engineer"}
- Skills: {", ".join(skills) if skills else "any"}
- Keywords: {keywords_text}
- {conditions_text}

User's profile for personalized matching:
- Interests: {interests_text}
- Expertise:
{expertise_text}

For each recommended job:
- Explain WHY it is a good match based on the user's SPECIFIC skills, expertise, and interests
- Reference the user's actual experience (e.g., "Your Terraform + IAP implementation experience matches...")
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
    profile: dict,
    preferences: JobPreferences | None = None,
    exclude_companies: list[str] | None = None,
) -> JobSearchResult:
    """Search for jobs using Perplexity API with built-in matching analysis.

    Args:
        profile: Developer profile from generate_profile()
        preferences: 求職者の希望条件
        exclude_companies: 除外する企業名リスト（追加検索時に使用）

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

    prompt = build_search_prompt(profile, preferences, exclude_companies)

    # 検索条件をログ出力
    tech_stack = profile.get("tech_stack", {})
    job_fit = profile.get("job_fit", {})
    roles = job_fit.get("ideal_roles", [])[:3]
    skills = (
        tech_stack.get("languages", [])[:3]
        + tech_stack.get("frameworks", [])[:3]
        + tech_stack.get("infrastructure", [])[:3]
    )
    keywords = job_fit.get("keywords", [])[:5]

    search_params = {
        "role": roles if roles else ["Software Engineer"],
        "skills": skills if skills else [],
        "keywords": keywords if keywords else [],
        "location": preferences.location,
        "salary_range": preferences.salary_range,
        "work_style": preferences.work_style or [],
        "job_type": preferences.job_type or [],
        "employment_type": preferences.employment_type or [],
        "other": preferences.other,
    }

    # Cloud Run環境では構造化ログ、ローカルでは整形して出力
    log_structured(logger, "求人検索開始", search_params=search_params)

    try:
        # Debug: APIキーの状態を確認
        logger.info(
            f"PERPLEXITY_API_KEY exists: {bool(api_key)}, len: {len(api_key) if api_key else 0}"
        )
        client = Perplexity(api_key=api_key)  # 明示的にAPIキーを渡す

        completion = client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "recommendations": {
                                "type": "array",
                                "minItems": 3,
                                "maxItems": 3,
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
        log_structured(
            logger,
            "Job search failed",
            level=logging.ERROR,
            exc_info=True,
            error=str(e),
        )
        return JobSearchResult(
            recommendations=[],
            status="error",
            error=str(e),
        )


def search_job_url(company: str, job_title: str, location: str = "") -> JobUrlResult:
    """特定の求人の詳細ページURLを検索.

    Args:
        company: 会社名
        job_title: 職種名
        location: 勤務地（オプション）

    Returns:
        JobUrlResult with URL and status
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return JobUrlResult(
            url=None,
            status="error",
            error="PERPLEXITY_API_KEY is required",
        )

    location_hint = f" in {location}" if location else ""
    prompt = f"""Find the job posting URL for "{job_title}" at "{company}"{location_hint}.

Search in this priority order:
1. BEST: Specific job detail page with job ID (e.g., /jobs/12345)
2. GOOD: Company's official recruitment page for this position
3. OK: Job listing on recruitment sites (HRMOS, Talentio, HERP, Green, Wantedly, Findy, Lapras, Forkwell, Indeed, etc.)

Return a JSON object:
{{
  "job_url": "https://example.com/jobs/12345"
}}

Priority examples (from best to acceptable):
1. https://hrmos.co/pages/company/jobs/12345 (specific job ID - BEST)
2. https://www.wantedly.com/projects/123456 (specific project - BEST)
3. https://herp.careers/v1/company/abcdef (specific job - BEST)
4. https://company.com/recruit/engineer (company's recruit page for engineers - GOOD)
5. https://hrmos.co/pages/company/jobs (company's job list - OK)

Do NOT return:
- Google search results
- General company homepage (without /recruit, /careers, /jobs path)

If you cannot find any relevant URL, return {{"job_url": null}}
"""

    try:
        client = Perplexity(api_key=api_key)  # 明示的にAPIキーを渡す

        completion = client.chat.completions.create(
            model="sonar",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "job_url": {"type": ["string", "null"]},
                        },
                        "required": ["job_url"],
                    }
                },
            },
        )

        content = completion.choices[0].message.content
        if not isinstance(content, str):
            return JobUrlResult(url=None, status="error", error="Unexpected response")

        result = json.loads(content)
        job_url = result.get("job_url")

        if job_url:
            return JobUrlResult(url=job_url, status="success")
        return JobUrlResult(url=None, status="not_found")

    except Exception as e:
        log_structured(
            logger,
            "Job URL search failed",
            level=logging.ERROR,
            exc_info=True,
            error=str(e),
        )
        return JobUrlResult(url=None, status="error", error=str(e))
