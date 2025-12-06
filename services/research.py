"""Job search using SerpAPI Google Jobs API."""

import os
from dataclasses import dataclass

from serpapi import GoogleSearch


@dataclass
class JobResult:
    """Job search result from SerpAPI."""

    title: str
    company_name: str
    location: str
    description: str
    job_link: str | None
    detected_extensions: dict | None  # salary, schedule, etc.


def build_search_query(profile: dict) -> str:
    """Build search query from developer profile."""
    keywords = profile.get("job_fit", {}).get("keywords", [])
    roles = profile.get("job_fit", {}).get("ideal_roles", [])
    tech_stack = profile.get("tech_stack", {})

    languages = tech_stack.get("languages", [])[:2]
    frameworks = tech_stack.get("frameworks", [])[:2]

    # Combine terms for search
    search_terms = roles[:2] + languages + frameworks + keywords[:2]
    return " ".join(search_terms[:6])  # Limit to avoid overly specific queries


def search_jobs(profile: dict, location: str = "Japan") -> dict:
    """Search for jobs using SerpAPI Google Jobs API.

    Args:
        profile: Developer profile from generate_profile()
        location: Job location (default: Japan)

    Returns:
        dict with query, jobs list, and status
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return {
            "query": "",
            "jobs": [],
            "status": "error",
            "error": "SERPAPI_API_KEY environment variable is required",
        }

    query = build_search_query(profile)

    params = {
        "engine": "google_jobs",
        "q": query,
        "location": location,
        "hl": "ja",  # Japanese language
        "api_key": api_key,
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        jobs_results = results.get("jobs_results", [])

        jobs = []
        for job in jobs_results[:10]:  # Limit to 10 results
            jobs.append(
                JobResult(
                    title=job.get("title", ""),
                    company_name=job.get("company_name", ""),
                    location=job.get("location", ""),
                    description=job.get("description", ""),
                    job_link=job.get("share_link")
                    or job.get("related_links", [{}])[0].get("link"),
                    detected_extensions=job.get("detected_extensions"),
                )
            )

        return {
            "query": query,
            "jobs": jobs,
            "status": "success",
            "total_results": len(jobs),
        }

    except Exception as e:
        return {
            "query": query,
            "jobs": [],
            "status": "error",
            "error": str(e),
        }
