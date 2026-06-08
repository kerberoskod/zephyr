import hashlib
import hmac
import pytest
from app.github_client import verify_webhook, GitHubClient


class TestVerifyWebhook:
    def test_valid_signature(self):
        payload = b'{"key": "value"}'
        secret = "my-secret"
        expected = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        assert verify_webhook(payload, expected, secret) is True

    def test_invalid_signature(self):
        payload = b'{"key": "value"}'
        secret = "my-secret"
        bad = "sha256=0000000000000000000000000000000000000000000000000000000000000000"
        assert verify_webhook(payload, bad, secret) is False

    def test_empty_signature(self):
        assert verify_webhook(b"test", "", "secret") is False

    def test_wrong_secret(self):
        payload = b"test"
        expected = "sha256=" + hmac.new(b"correct", payload, hashlib.sha256).hexdigest()
        assert verify_webhook(payload, expected, "wrong") is False

    def test_empty_payload_and_secret(self):
        sig = "sha256=" + hmac.new(b"", b"", hashlib.sha256).hexdigest()
        assert verify_webhook(b"", sig, "") is True


class TestGitHubClient:
    @pytest.fixture
    def gh(self):
        return GitHubClient(token="gh_test_token")

    async def test_get_pr_diff_success(self, gh, httpx_mock):
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            text="diff --git a/file.py b/file.py\nindex abc..def 100644\n--- a/file.py\n+++ b/file.py\n@@ -1 +1 @@\n-old\n+new",
            headers={"Content-Type": "text/plain"},
        )
        diff = await gh.get_pr_diff("owner/repo", 1)
        assert diff is not None
        assert "diff --git" in diff

    async def test_get_pr_diff_not_found(self, gh, httpx_mock):
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/999",
            status_code=404,
        )
        diff = await gh.get_pr_diff("owner/repo", 999)
        assert diff is None

    async def test_get_pr_details_success(self, gh, httpx_mock):
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/1",
            json={"title": "Fix bug", "user": {"login": "dev"}},
        )
        details = await gh.get_pr_details("owner/repo", 1)
        assert details is not None
        assert details["title"] == "Fix bug"

    async def test_get_pr_details_not_found(self, gh, httpx_mock):
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/pulls/999",
            status_code=404,
        )
        details = await gh.get_pr_details("owner/repo", 999)
        assert details is None

    async def test_post_comment_success(self, gh, httpx_mock):
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/issues/1/comments",
            status_code=201,
            json={"id": 1},
        )
        result = await gh.post_comment("owner/repo", 1, "LGTM")
        assert result is True

    async def test_post_comment_failure(self, gh, httpx_mock):
        httpx_mock.add_response(
            url="https://api.github.com/repos/owner/repo/issues/1/comments",
            status_code=403,
            json={"message": "Forbidden"},
        )
        result = await gh.post_comment("owner/repo", 1, "LGTM")
        assert result is False

    async def test_close(self, gh):
        await gh.close()

    async def test_headers_include_token(self):
        gh = GitHubClient(token="test-token")
        assert gh.headers["Authorization"] == "Bearer test-token"
        assert gh.headers["User-Agent"] == "zephyr-code-review"
