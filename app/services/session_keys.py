"""Session state cache keys."""

# Auth/session state
ACCESS_TOKEN = "access_token"
SESSION_ID = "session_id"
USER = "user"

# Profile view/session state
PROFILE_STATE = "profile"
REPO_METADATA_LIST = "repo_metadata_list"
SELECTED_REPOS = "selected_repos"
REGEN_REPO_METADATA_LIST = "regen_repo_metadata_list"
REGEN_SELECTED_REPOS = "regen_selected_repos"

# Job search/session state
SETTINGS_LOADED = "settings_loaded"
JOB_LOCATION = "job_location"
SALARY_RANGE = "salary_range"
WORK_STYLE = "work_style"
JOB_TYPE = "job_type"
EMPLOYMENT_TYPE = "employment_type"
OTHER_PREFERENCES = "other_preferences"

# Firestore キャッシュ用キー（再レンダリング時のFirestore呼び出し削減用）
QUOTA_STATUS = "_cache_quota_status"
PROFILE = "_cache_profile"
USER_SETTINGS = "_cache_user_settings"

# 検索結果キャッシュ
JOB_RESULTS = "_cache_job_results"
JOB_PREFERENCES = "_cache_job_preferences"  # 検索条件（追加検索用）

# Onboarding
SHOW_PROFILE_SUCCESS = "_show_profile_success"

# Logout flow
LOGOUT_REQUESTED = "_logout_requested"
