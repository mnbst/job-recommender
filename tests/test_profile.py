"""Tests for services/profile.py."""

from unittest.mock import MagicMock, patch

from langchain_core.output_parsers import PydanticOutputParser

from services.github import RepoInfo
from services.profile import (
    DeveloperProfile,
    JobFit,
    NotableProject,
    SkillAssessment,
    TechStack,
    generate_profile,
)


class TestPydanticModels:
    """Tests for Pydantic models."""

    def test_tech_stack_creation(self):
        """Test TechStack model creation."""
        tech = TechStack(
            languages=["Python", "Go"],
            frameworks=["FastAPI"],
            infrastructure=["Docker"],
        )
        assert tech.languages == ["Python", "Go"]
        assert tech.frameworks == ["FastAPI"]
        assert tech.infrastructure == ["Docker"]

    def test_skill_assessment_creation(self):
        """Test SkillAssessment model creation."""
        assessment = SkillAssessment(
            code_quality="高い",
            design_ability="優秀",
            completion_rate="良好",
        )
        assert assessment.code_quality == "高い"

    def test_notable_project_creation(self):
        """Test NotableProject model creation."""
        project = NotableProject(name="my-project", highlight="特筆点")
        assert project.name == "my-project"
        assert project.highlight == "特筆点"

    def test_job_fit_creation(self):
        """Test JobFit model creation."""
        job_fit = JobFit(
            ideal_roles=["エンジニア"],
            company_types=["スタートアップ"],
            keywords=["Python"],
        )
        assert job_fit.ideal_roles == ["エンジニア"]

    def test_developer_profile_creation(self, sample_profile: DeveloperProfile):
        """Test DeveloperProfile model creation."""
        assert sample_profile.tech_stack.languages == ["Python", "TypeScript", "Go"]
        assert "バックエンド開発" in sample_profile.expertise_areas
        assert sample_profile.summary is not None


class TestPydanticOutputParser:
    """Tests for PydanticOutputParser with DeveloperProfile."""

    def test_parser_format_instructions(self):
        """Test that parser generates format instructions."""
        parser = PydanticOutputParser(pydantic_object=DeveloperProfile)
        instructions = parser.get_format_instructions()

        assert "tech_stack" in instructions
        assert "expertise_areas" in instructions
        assert "summary" in instructions

    def test_parser_parse_valid_json(self):
        """Test parsing valid JSON response."""
        parser = PydanticOutputParser(pydantic_object=DeveloperProfile)

        valid_json = """{
            "tech_stack": {
                "languages": ["Python"],
                "frameworks": ["FastAPI"],
                "infrastructure": ["Docker"]
            },
            "expertise_areas": ["バックエンド"],
            "skill_assessment": {
                "code_quality": "高い",
                "design_ability": "良い",
                "completion_rate": "高い"
            },
            "notable_projects": [
                {"name": "project1", "highlight": "特筆点"}
            ],
            "interests": ["AI"],
            "job_fit": {
                "ideal_roles": ["エンジニア"],
                "company_types": ["スタートアップ"],
                "keywords": ["Python"]
            },
            "summary": "優秀なエンジニア"
        }"""

        result = parser.parse(valid_json)
        assert isinstance(result, DeveloperProfile)
        assert result.tech_stack.languages == ["Python"]

    def test_parser_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code block."""
        parser = PydanticOutputParser(pydantic_object=DeveloperProfile)

        markdown_json = """```json
{
    "tech_stack": {
        "languages": ["Go"],
        "frameworks": [],
        "infrastructure": []
    },
    "expertise_areas": [],
    "skill_assessment": {
        "code_quality": "良い",
        "design_ability": "良い",
        "completion_rate": "良い"
    },
    "notable_projects": [],
    "interests": [],
    "job_fit": {
        "ideal_roles": [],
        "company_types": [],
        "keywords": []
    },
    "summary": "テスト"
}
```"""

        result = parser.parse(markdown_json)
        assert isinstance(result, DeveloperProfile)
        assert result.tech_stack.languages == ["Go"]


class TestGenerateProfile:
    """Tests for generate_profile function."""

    @patch("services.profile.GenerativeModel")
    @patch("services.profile.init_vertex_ai")
    def test_generate_profile_success(
        self,
        mock_init: MagicMock,
        mock_model_class: MagicMock,
        sample_repos: list[RepoInfo],
    ):
        """Test successful profile generation."""
        mock_response = MagicMock()
        mock_response.text = """{
            "tech_stack": {
                "languages": ["TypeScript", "Python"],
                "frameworks": ["React", "FastAPI"],
                "infrastructure": ["Docker"]
            },
            "expertise_areas": ["フルスタック開発"],
            "skill_assessment": {
                "code_quality": "高品質",
                "design_ability": "優秀",
                "completion_rate": "高い"
            },
            "notable_projects": [
                {"name": "web-app", "highlight": "モダンな技術スタック"}
            ],
            "interests": ["Web開発"],
            "job_fit": {
                "ideal_roles": ["フルスタックエンジニア"],
                "company_types": ["スタートアップ"],
                "keywords": ["React", "Python"]
            },
            "summary": "フルスタック開発者"
        }"""

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        result = generate_profile(sample_repos)

        assert isinstance(result, dict)
        assert "tech_stack" in result
        assert "TypeScript" in result["tech_stack"]["languages"]
        mock_init.assert_called_once()

    @patch("services.profile.GenerativeModel")
    @patch("services.profile.init_vertex_ai")
    def test_generate_profile_with_empty_repos(
        self,
        mock_init: MagicMock,
        mock_model_class: MagicMock,
    ):
        """Test profile generation with empty repos list."""
        mock_response = MagicMock()
        mock_response.text = """{
            "tech_stack": {
                "languages": [],
                "frameworks": [],
                "infrastructure": []
            },
            "expertise_areas": [],
            "skill_assessment": {
                "code_quality": "不明",
                "design_ability": "不明",
                "completion_rate": "不明"
            },
            "notable_projects": [],
            "interests": [],
            "job_fit": {
                "ideal_roles": [],
                "company_types": [],
                "keywords": []
            },
            "summary": "リポジトリ情報なし"
        }"""

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model

        result = generate_profile([])

        assert isinstance(result, dict)
        assert result["tech_stack"]["languages"] == []
