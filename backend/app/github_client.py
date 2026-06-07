import hashlib
import hmac
import httpx


GITHUB_API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "zephyr-code-review",
        }

    async def get_pr_diff(self, repo_full_name: str, pr_number: int) -> str | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}",
                headers=self.headers,
            )
            if resp.status_code != 200:
                return None
            return resp.text

    async def get_pr_details(self, repo_full_name: str, pr_number: int) -> dict | None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}",
                headers={**self.headers, "Accept": "application/vnd.github.v3+json"},
            )
            if resp.status_code != 200:
                return None
            return resp.json()

    async def post_comment(
        self, repo_full_name: str, pr_number: int, body: str
    ) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}/comments",
                headers={**self.headers, "Accept": "application/vnd.github.v3+json"},
                json={"body": body},
            )
            return resp.status_code == 201

    async def post_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str,
        commit_id: str,
        path: str,
        line: int,
    ) -> bool:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{GITHUB_API}/repos/{repo_full_name}/pulls/{pr_number}/comments",
                headers={**self.headers, "Accept": "application/vnd.github.v3+json"},
                json={
                    "body": body,
                    "commit_id": commit_id,
                    "path": path,
                    "line": line,
                },
            )
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
