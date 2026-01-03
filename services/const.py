"""定数定義."""

import os

# =============================================================================
# Session
# =============================================================================
SESSION_TTL_DAYS = 7
SESSION_COOKIE_NAME = "job_recommender_session"
MAX_COOKIE_RETRIES = 3

# =============================================================================
# Cache
# =============================================================================
CACHE_TTL_DAYS = int(os.getenv("PROFILE_CACHE_TTL_DAYS", "7"))

# =============================================================================
# GitHub OAuth
# =============================================================================
GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
