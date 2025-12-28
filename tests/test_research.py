"""Tests for services/research.py."""

from unittest.mock import MagicMock, patch

from services.research import (
    JobPreferences,
    JobRecommendation,
    JobSearchResult,
    JobSource,
    MatchReason,
    build_search_prompt,
    search_jobs,
)


class TestDataClasses:
    """Tests for research.py dataclasses."""

    def test_job_source_creation(self):
        """Test JobSource dataclass creation."""
        source = JobSource(url="https://example.com/job", used_for="salary")
        assert source.url == "https://example.com/job"
        assert source.used_for == "salary"

    def test_match_reason_creation(self):
        """Test MatchReason dataclass creation."""
        reason = MatchReason(
            summary="良いマッチです",
            matched_conditions=["勤務地が東京", "年収1000万以上"],
            why_good="スキルがマッチしています",
        )
        assert reason.summary == "良いマッチです"
        assert len(reason.matched_conditions) == 2

    def test_job_recommendation_creation(self):
        """Test JobRecommendation dataclass creation."""
        rec = JobRecommendation(
            job_title="Senior Engineer",
            company="Tech Corp",
            location="Tokyo",
            salary_range="10M-15M JPY",
            reason=MatchReason(
                summary="マッチ",
                matched_conditions=["条件1"],
                why_good="理由",
            ),
            sources=[JobSource(url="https://example.com", used_for="info")],
        )
        assert rec.job_title == "Senior Engineer"
        assert rec.company == "Tech Corp"
        assert rec.salary_range == "10M-15M JPY"

    def test_job_search_result_success(self):
        """Test JobSearchResult with success status."""
        result = JobSearchResult(
            recommendations=[],
            status="success",
        )
        assert result.status == "success"
        assert result.error is None

    def test_job_search_result_error(self):
        """Test JobSearchResult with error status."""
        result = JobSearchResult(
            recommendations=[],
            status="error",
            error="API Error",
        )
        assert result.status == "error"
        assert result.error == "API Error"


class TestBuildSearchPrompt:
    """Tests for build_search_prompt function."""

    def test_build_prompt_with_full_profile(self, sample_profile_dict: dict):
        """Test prompt building with complete profile."""
        prompt = build_search_prompt(sample_profile_dict, JobPreferences(location="Tokyo"))

        assert "Tokyo" in prompt
        assert "Python" in prompt or "TypeScript" in prompt
        assert "バックエンドエンジニア" in prompt or "フルスタックエンジニア" in prompt

    def test_build_prompt_with_empty_profile(self):
        """Test prompt building with empty profile."""
        empty_profile: dict = {
            "tech_stack": {"languages": [], "frameworks": []},
            "job_fit": {"ideal_roles": []},
        }
        prompt = build_search_prompt(empty_profile, JobPreferences(location="Japan"))

        assert "Japan" in prompt
        assert "Software Engineer" in prompt  # Default role
        assert "any" in prompt  # Default skills

    def test_build_prompt_location(self):
        """Test prompt includes specified location."""
        profile: dict = {
            "tech_stack": {"languages": ["Python"], "frameworks": ["Django"]},
            "job_fit": {"ideal_roles": ["Backend Engineer"]},
        }
        prompt = build_search_prompt(profile, JobPreferences(location="San Francisco"))

        assert "San Francisco" in prompt


class TestSearchJobs:
    """Tests for search_jobs function."""

    def test_search_jobs_no_api_key(self, sample_profile_dict: dict):
        """Test search_jobs returns error when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            result = search_jobs(sample_profile_dict)

        assert result.status == "error"
        assert "PERPLEXITY_API_KEY" in (result.error or "")
        assert result.recommendations == []

    @patch("services.research.Perplexity")
    def test_search_jobs_success(
        self,
        mock_perplexity_class: MagicMock,
        sample_profile_dict: dict,
    ):
        """Test successful job search."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content="""{
                        "recommendations": [
                            {
                                "job_title": "Senior Python Engineer",
                                "company": "Tech Corp",
                                "location": "Tokyo",
                                "salary_range": "10M-14M JPY",
                                "reason": {
                                    "summary": "Pythonスキルがマッチ",
                                    "matched_conditions": ["勤務地が東京"],
                                    "why_good": "経験が活かせます"
                                },
                                "sources": [
                                    {"url": "https://example.com/job/1", "used_for": "求人情報"}
                                ]
                            }
                        ]
                    }"""
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_perplexity_class.return_value = mock_client

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            result = search_jobs(sample_profile_dict, JobPreferences(location="Tokyo"))

        assert result.status == "success"
        assert len(result.recommendations) == 1
        assert result.recommendations[0].job_title == "Senior Python Engineer"
        assert result.recommendations[0].company == "Tech Corp"

    @patch("services.research.Perplexity")
    def test_search_jobs_api_error(
        self,
        mock_perplexity_class: MagicMock,
        sample_profile_dict: dict,
    ):
        """Test search_jobs handles API errors."""
        mock_perplexity_class.side_effect = Exception("API connection failed")

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            result = search_jobs(sample_profile_dict)

        assert result.status == "error"
        assert "API connection failed" in (result.error or "")
        assert result.recommendations == []

    @patch("services.research.Perplexity")
    def test_search_jobs_empty_recommendations(
        self,
        mock_perplexity_class: MagicMock,
        sample_profile_dict: dict,
    ):
        """Test search_jobs handles empty recommendations."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"recommendations": []}'))
        ]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_perplexity_class.return_value = mock_client

        with patch.dict("os.environ", {"PERPLEXITY_API_KEY": "test-key"}):
            result = search_jobs(sample_profile_dict)

        assert result.status == "success"
        assert result.recommendations == []
