"""Deep Research integration for job search."""

import os

from google.cloud import discoveryengine_v1 as discoveryengine


def search_jobs(profile: dict) -> dict:
    """Search for jobs using Deep Research based on developer profile.

    Note: This requires Discovery Engine with Deep Research enabled.
    You need to:
    1. Create a Discovery Engine app with web search enabled
    2. Get allowlist access for Deep Research API
    """
    project_id = os.getenv("GCP_PROJECT_ID")
    # app_id needs to be created in Discovery Engine console
    app_id = os.getenv("DISCOVERY_ENGINE_APP_ID", "job-search-app")

    # Build search query from profile
    keywords = profile.get("job_fit", {}).get("keywords", [])
    roles = profile.get("job_fit", {}).get("ideal_roles", [])
    tech_stack = profile.get("tech_stack", {})

    languages = tech_stack.get("languages", [])
    frameworks = tech_stack.get("frameworks", [])

    search_terms = keywords + roles + languages[:3] + frameworks[:3]
    query = f"求人 エンジニア {' '.join(search_terms)}"

    # Initialize client
    client = discoveryengine.ConversationalSearchServiceClient()

    # Build request for Deep Research
    # Note: This is the streamAssist endpoint for Deep Research
    parent = (
        f"projects/{project_id}/locations/global/collections/default_collection"
        f"/engines/{app_id}/assistants/default_assistant"
    )

    request = discoveryengine.ConverseConversationRequest(
        name=parent,
        query=discoveryengine.TextInput(input=query),
    )

    try:
        response = client.converse_conversation(request=request)
        return {
            "query": query,
            "results": response.reply.text if response.reply else "",
            "status": "success"
        }
    except Exception as e:
        # Fallback for when Deep Research is not available
        return {
            "query": query,
            "results": None,
            "status": "error",
            "error": str(e),
            "message": "Deep Research APIが利用できません。Discovery Engineのセットアップを確認してください。"
        }
