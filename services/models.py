"""Shared models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GitHubUser(BaseModel):
    """GitHubユーザー情報."""

    id: int
    login: str
    name: str | None
    email: str | None
    avatar_url: str


class FileContent(BaseModel):
    """File content from repository."""

    path: str
    content: str


class RepoMetadata(BaseModel):
    """Lightweight repository metadata for selection UI."""

    name: str
    full_name: str
    description: str | None
    language: str | None
    stars: int
    is_fork: bool


class RepoInfo(BaseModel):
    """Repository information extracted from GitHub."""

    name: str
    description: str | None
    language: str | None
    languages: dict[str, int]
    topics: list[str]
    readme: str | None
    stars: int
    forks: int
    updated_at: str
    is_fork: bool = False
    file_structure: list[str] = Field(default_factory=list)
    dependency_files: list[FileContent] = Field(default_factory=list)
    main_files: list[FileContent] = Field(default_factory=list)
    config_files: list[str] = Field(default_factory=list)


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


class JobSource(BaseModel):
    """Source URL for job information."""

    url: str
    used_for: str


class MatchReason(BaseModel):
    """Explanation for why a job is a good match."""

    summary: str
    matched_conditions: list[str]
    why_good: str


class JobRecommendation(BaseModel):
    """Job recommendation from Perplexity API."""

    job_title: str
    company: str
    location: str
    salary_range: str | None
    reason: MatchReason
    sources: list[JobSource]


class JobSearchResult(BaseModel):
    """Result from Perplexity job search."""

    recommendations: list[JobRecommendation]
    status: str
    error: str | None = None


class JobPreferences(BaseModel):
    """求職者の希望条件."""

    location: str = "東京"
    salary_range: str = "指定なし"
    work_style: list[str] | None = None
    job_type: list[str] | None = None
    employment_type: list[str] | None = None
    other: str = ""


class JobUrlResult(BaseModel):
    """求人URL検索結果."""

    url: str | None
    status: str
    error: str | None = None


class UserSettings(BaseModel):
    """ユーザー設定."""

    repo_limit: int = 10
    job_location: str = "東京"
    salary_range: str = "指定なし"
    work_style: list[str] = Field(default_factory=list)
    job_type: list[str] = Field(default_factory=list)
    employment_type: list[str] = Field(default_factory=list)
    other_preferences: str = ""
    plan: str = "free"  # "free" | "premium"


class QuotaStatus(BaseModel):
    """ユーザーのクォータ状態."""

    credits: int  # 残りクレジット
    can_use: bool  # クレジットが残っているか
