import json
import hashlib
import hmac
import pytest
from unittest.mock import patch


def sign(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


class TestWebhook:
    async def test_missing_signature(self, client):
        resp = await client.post(
            "/api/webhook",
            json={"action": "opened", "pull_request": {"number": 1}},
        )
        assert resp.status_code == 401

    async def test_invalid_signature(self, client):
        payload = json.dumps({"action": "opened"}).encode()
        resp = await client.post(
            "/api/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=00",
                "X-GitHub-Event": "pull_request",
            },
        )
        assert resp.status_code == 401

    async def test_valid_pr_opened(self, client):
        payload = json.dumps({
            "action": "opened",
            "pull_request": {"number": 1, "title": "Fix", "user": {"login": "dev"}},
            "repository": {"full_name": "kerberoskod/test-repo"},
            "installation": {"id": 99},
        }).encode()
        sig = sign(payload, "test-secret")

        with patch("app.webhook.process_review") as mock_process:
            resp = await client.post(
                "/api/webhook",
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Hub-Signature-256": sig,
                    "X-GitHub-Event": "pull_request",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"

    async def test_ignores_non_pr_events(self, client):
        payload = json.dumps({"action": "created"}).encode()
        sig = sign(payload, "test-secret")
        resp = await client.post(
            "/api/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "issues",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    async def test_ignores_unsupported_actions(self, client):
        payload = json.dumps({
            "action": "closed",
            "pull_request": {"number": 1},
            "repository": {"full_name": "owner/repo"},
            "installation": {"id": 1},
        }).encode()
        sig = sign(payload, "test-secret")
        resp = await client.post(
            "/api/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "pull_request",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    async def test_missing_required_fields(self, client):
        payload = json.dumps({"action": "opened", "pull_request": {"number": 1}}).encode()
        sig = sign(payload, "test-secret")
        resp = await client.post(
            "/api/webhook",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": sig,
                "X-GitHub-Event": "pull_request",
            },
        )
        assert resp.status_code == 400
