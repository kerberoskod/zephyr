import datetime

from app.config import settings
from app.github_client import GitHubClient
from app.reviewer import Reviewer
from app.models import Review, async_session


async def process_review(repo: str, pr_number: int, installation_token: str):
    async with async_session() as session:
        review = Review(
            repo_full_name=repo,
            pr_number=pr_number,
            status="processing",
        )
        session.add(review)
        await session.commit()
        review_id = review.id

    gh = GitHubClient(installation_token)
    reviewer = Reviewer()

    try:
        diff = await gh.get_pr_diff(repo, pr_number)
        if not diff:
            raise ValueError("Could not fetch PR diff")

        details = await gh.get_pr_details(repo, pr_number)
        pr_title = (details or {}).get("title", "")
        pr_author = ((details or {}).get("user") or {}).get("login", "") if details else ""

        result = await reviewer.review_diff(diff)
        summary = result.get("summary", "")
        findings = result.get("findings", [])

        async with async_session() as session:
            review = await session.get(Review, review_id)
            if review:
                review.status = "completed"
                review.pr_title = pr_title
                review.pr_author = pr_author
                review.diff_summary = summary
                review.findings = findings
                review.total_comments = len(findings)
                review.completed_at = datetime.datetime.utcnow()
                await session.commit()

        critical = [f for f in findings if f.get("severity") == "critical"]
        major = [f for f in findings if f.get("severity") == "major"]

        body = f"### Zephyr Code Review\n\n"
        body += f"**Summary:** {summary}\n\n"
        body += f"**Findings:** {len(findings)} total"
        if critical:
            body += f" ({len(critical)} critical"
            if major:
                body += f", {len(major)} major"
            body += ")"
        elif major:
            body += f" ({len(major)} major)"
        body += "\n\n"

        for f in findings[:10]:
            icon = {"critical": "🔴", "major": "🟡", "minor": "🔵"}
            body += f"{icon.get(f.get('severity', 'minor'), '⚪')} **{f.get('severity', 'minor').upper()}** "
            body += f"| {f.get('category', 'other')} | {f.get('file', '?')}:{f.get('line', '?')}\n"
            body += f"> {f.get('message', '')}\n\n"

        if len(findings) > 10:
            body += f"*...and {len(findings) - 10} more findings. See dashboard for full details.*\n"

        await gh.post_comment(repo, pr_number, body)

    except Exception as e:
        async with async_session() as session:
            review = await session.get(Review, review_id) if "review_id" in dir() else None
            if review is None:
                review = Review(repo_full_name=repo, pr_number=pr_number, status="failed", error=str(e))
                session.add(review)
            else:
                review.status = "failed"
                review.error = str(e)
            await session.commit()
