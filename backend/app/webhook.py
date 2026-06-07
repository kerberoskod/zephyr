from fastapi import APIRouter, Request, HTTPException
from app.github_client import verify_webhook, get_installation_token
from app.config import settings
from app.worker import process_review
import json

router = APIRouter()


@router.post("/webhook")
async def github_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")
    event = request.headers.get("x-github-event", "")

    if settings.github_webhook_secret:
        if not verify_webhook(body, signature, settings.github_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid signature")

    if event != "pull_request":
        return {"status": "ignored", "event": event}

    data = json.loads(body)
    action = data.get("action")

    if action not in ("opened", "synchronize", "reopened"):
        return {"status": "ignored", "action": action}

    pr = data.get("pull_request", {})
    repo = data.get("repository", {})
    repo_full_name = repo.get("full_name", "")
    pr_number = pr.get("number")
    installation_id = data.get("installation", {}).get("id")

    if not repo_full_name or not pr_number or not installation_id:
        raise HTTPException(status_code=400, detail="Missing required fields")

    token = None
    if settings.github_app_id and settings.github_private_key:
        token = await get_installation_token(
            int(settings.github_app_id), settings.github_private_key, installation_id
        )

    import asyncio
    asyncio.create_task(
        process_review(repo_full_name, pr_number, token or "")
    )

    return {"status": "queued", "repo": repo_full_name, "pr": pr_number}
