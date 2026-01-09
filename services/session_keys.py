"""Session state cache keys."""

# Firestore キャッシュ用キー（再レンダリング時のFirestore呼び出し削減用）
QUOTA_STATUS = "_cache_quota_status"
PROFILE = "_cache_profile"
USER_SETTINGS = "_cache_user_settings"

# 検索結果キャッシュ
JOB_RESULTS = "_cache_job_results"
JOB_PREFERENCES = "_cache_job_preferences"  # 検索条件（追加検索用）
