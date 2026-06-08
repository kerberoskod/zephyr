import pytest
from unittest.mock import AsyncMock, patch
from app.worker import get_or_create_review, process_review
from app.models import Review
from app.github_client import GitHubClient
from app.reviewer import Reviewer


class TestGetOrCreateReview:
    async def test_creates_new_review(self, session):
        review = await get_or_create_review(session, "owner/repo", 1)
        assert review.id is not None
        assert review.status == "processing"
        assert review.repo_full_name == "owner/repo"
        assert review.pr_number == 1

    async def test_resets_existing_review(self, session):
        review = Review(repo_full_name="owner/repo", pr_number=1, status="completed", error="old error")
        session.add(review)
        await session.commit()

        updated = await get_or_create_review(session, "owner/repo", 1)
        assert updated.id == review.id
        assert updated.status == "processing"
        assert updated.error is None

    async def test_unique_constraint_separate_prs(self, session):
        r1 = await get_or_create_review(session, "owner/repo", 1)
        r2 = await get_or_create_review(session, "owner/repo", 2)
        assert r1.id != r2.id


class TestProcessReview:
    async def test_successful_review(self):
        mock_diff = "diff --git a/x.py b/x.py\nindex abc..def\n--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-old\n+new"
        mock_details = {"title": "Fix bug", "user": {"login": "coder"}}
        mock_result = {"summary": "Good code", "findings": [{"severity": "minor", "category": "style", "message": "nit"}]}

        mock_session = AsyncMock()
        mock_session_get = AsyncMock()

        with (
            patch("app.worker.async_session") as mock_async_session,
            patch("app.worker.GitHubClient", spec=GitHubClient) as MockGH,
            patch("app.worker.Reviewer", spec=Reviewer) as MockReviewer,
        ):
            mock_async_session.return_value.__aenter__.return_value = mock_session

            mock_gh_instance = MockGH.return_value
            mock_gh_instance.get_pr_diff = AsyncMock(return_value=mock_diff)
            mock_gh_instance.get_pr_details = AsyncMock(return_value=mock_details)
            mock_gh_instance.post_comment = AsyncMock(return_value=True)
            mock_gh_instance.close = AsyncMock(return_value=None)

            mock_reviewer_instance = MockReviewer.return_value
            mock_reviewer_instance.review_diff = AsyncMock(return_value=mock_result)

            async def fake_get_or_create(session, repo, pr_number):
                review = Review(repo_full_name=repo, pr_number=pr_number, status="processing", id="test-id")
                return review

            with patch("app.worker.get_or_create_review", fake_get_or_create):
                await process_review("owner/repo", 1, "token")

            mock_gh_instance.get_pr_diff.assert_called_once_with("owner/repo", 1)
            mock_gh_instance.get_pr_details.assert_called_once_with("owner/repo", 1)
            mock_reviewer_instance.review_diff.assert_called_once_with(mock_diff)
            mock_gh_instance.post_comment.assert_called_once()
            mock_gh_instance.close.assert_called_once()

    async def test_handles_fetch_diff_failure(self):
        async def fake_get_or_create(session, repo, pr_number):
            return Review(repo_full_name=repo, pr_number=pr_number, status="processing", id="err-id")

        mock_session = AsyncMock()

        with (
            patch("app.worker.async_session") as mock_async_session,
            patch("app.worker.GitHubClient", spec=GitHubClient) as MockGH,
            patch("app.worker.Reviewer", spec=Reviewer) as MockReviewer,
        ):
            mock_async_session.return_value.__aenter__.return_value = mock_session
            mock_gh_instance = MockGH.return_value
            mock_gh_instance.get_pr_diff = AsyncMock(return_value=None)
            mock_gh_instance.close = AsyncMock(return_value=None)

            with patch("app.worker.get_or_create_review", fake_get_or_create):
                await process_review("owner/repo", 1, "token")

            mock_gh_instance.close.assert_called_once()

    async def test_handles_review_exception(self):
        async def fake_get_or_create(session, repo, pr_number):
            return Review(repo_full_name=repo, pr_number=pr_number, status="processing", id="exc-id")

        mock_session = AsyncMock()

        with (
            patch("app.worker.async_session") as mock_async_session,
            patch("app.worker.GitHubClient", spec=GitHubClient) as MockGH,
            patch("app.worker.Reviewer", spec=Reviewer) as MockReviewer,
        ):
            mock_async_session.return_value.__aenter__.return_value = mock_session
            mock_gh_instance = MockGH.return_value
            mock_gh_instance.get_pr_diff = AsyncMock(side_effect=Exception("API error"))
            mock_gh_instance.close = AsyncMock(return_value=None)

            with patch("app.worker.get_or_create_review", fake_get_or_create):
                await process_review("owner/repo", 1, "token")

            mock_gh_instance.close.assert_called_once()
