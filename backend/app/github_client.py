import hashlib
import hmac
import httpx
import logging

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "zephyr-code-review",
        }
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def close(self):
        await self._client.aclose()

    async def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str | None:
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        resp = await self._client.get(
            f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}",
            headers=headers,
        )
        if resp.status_code != 200:
            return None
        return resp.text

    async def get_pr_details(self, repo_full_name: str, pr_number: int) -> dict | None:
        headers = {**self.headers, "Accept": "application/vnd.github.v3+json"}
        resp = await self._client.get(
            f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}",
            headers=headers,
        )
        if resp.status_code != 200:
            return None
        return resp.json()

    async def post_comment(
        self, repo_full_name: str, pr_number: int, body: str
    ) -> bool:
        headers = {**self.headers, "Accept": "application/vnd.github.v3+json"}
        resp = await self._client.post(
            f"{GITHUB_API}/repos/{repo_full_name}/issues/{pr_number}/comments",
            headers=headers,
            json={"body": body},
        )
        if resp.status_code != 201:
            logger.error("Failed to post comment: %d %s", resp.status_code, resp.text)
        return resp.status_code == 201

async def get_installation_token(app_id: int, private_key: str, installation_id: int) -> str | None:
    import asyncio
    import logging
    logger = logging.getLogger(__name__)
    try:
        from github import GithubIntegration
        integration = GithubIntegration(app_id, private_key)
        token = await asyncio.to_thread(
            lambda: integration.get_access_token(installation_id).token
        )
        return token
    except Exception as e:
        logger.exception("Failed to get installation token for installation %s: %s", installation_id, e)
        return None


def verify_webhook(payload_body: bytes, signature: str, secret: str) -> bool:
    if not signature:
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
