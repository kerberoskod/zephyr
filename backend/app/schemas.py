import datetime
from pydantic import BaseModel


class ReviewResponse(BaseModel):
    id: str
    repo_full_name: str
    pr_number: int
    pr_title: str | None = None
    pr_author: str | None = None
    status: str
    diff_summary: str | None = None
    findings: list | None = None
    error: str | None = None
    total_comments: int = 0
    created_at: datetime.datetime | None = None
    completed_at: datetime.datetime | None = None


class ReviewListResponse(BaseModel):
    reviews: list[ReviewResponse]
    total: int


class WebhookPayload(BaseModel):
    action: str
    pull_request: dict | None = None
    repository: dict | None = None
