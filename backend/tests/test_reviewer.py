import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.reviewer import Reviewer


class TestReviewer:
    @pytest.fixture(autouse=True)
    def env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-key")

    @pytest.fixture
    def reviewer(self):
        return Reviewer()

    async def test_review_diff_returns_findings(self, reviewer):
        fake_response = MagicMock()
        fake_response.content = [
            MagicMock(text=json.dumps({
                "summary": "Looks good",
                "findings": [
                    {"severity": "minor", "category": "style", "message": "Add spaces",
                     "file": "src/main.py", "line": 10, "suggestion": "PEP 8"},
                ],
            }), type="text")
        ]

        with patch.object(reviewer.client.messages, "create", AsyncMock(return_value=fake_response)):
            result = await reviewer.review_diff("## Diff\nsome code\n")

        assert result["summary"] == "Looks good"
        assert len(result["findings"]) == 1
        assert result["findings"][0]["severity"] == "minor"

    async def test_review_diff_handles_empty_diff(self, reviewer):
        fake_response = MagicMock()
        fake_response.content = [
            MagicMock(text=json.dumps({"summary": "", "findings": []}), type="text")
        ]

        with patch.object(reviewer.client.messages, "create", AsyncMock(return_value=fake_response)):
            result = await reviewer.review_diff("")

        assert result["findings"] == []

    async def test_review_diff_truncates_large_diff(self, reviewer):
        large_diff = "a" * 200_000

        fake_response = MagicMock()
        fake_response.content = [
            MagicMock(text=json.dumps({"summary": "truncated", "findings": []}), type="text")
        ]

        with patch.object(reviewer.client.messages, "create", AsyncMock(return_value=fake_response)) as mock_create:
            result = await reviewer.review_diff(large_diff)

        assert result["summary"] == "truncated"
        call_diff = mock_create.call_args[1]["messages"][0]["content"]
        diff_start = call_diff.find("<diff>\n") + len("<diff>\n")
        diff_end = call_diff.rfind("\n</diff>")
        actual_diff = call_diff[diff_start:diff_end]
        assert len(actual_diff) <= 100_000

    async def test_review_diff_strips_markdown_code_block(self, reviewer):
        fake_response = MagicMock()
        fake_response.content = [
            MagicMock(text="```json\n{\"summary\": \"clean\", \"findings\": []}\n```", type="text")
        ]

        with patch.object(reviewer.client.messages, "create", AsyncMock(return_value=fake_response)):
            result = await reviewer.review_diff("diff")

        assert result["summary"] == "clean"

    async def test_review_diff_handles_malformed_json(self, reviewer):
        fake_response = MagicMock()
        fake_response.content = [MagicMock(text="not json", type="text")]

        with patch.object(reviewer.client.messages, "create", AsyncMock(return_value=fake_response)):
            result = await reviewer.review_diff("diff")

        assert "error" in result or result["findings"] == []
