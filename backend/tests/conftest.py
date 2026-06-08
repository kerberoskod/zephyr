import os

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-key")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-secret")
os.environ.setdefault("GITHUB_APP_ID", "12345")
os.environ.setdefault("GITHUB_PRIVATE_KEY", "test-private-key")

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.models import Base


@pytest.fixture
async def engine():
    e = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with e.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield e
    await e.dispose()


@pytest.fixture
async def session(engine):
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        yield s


@pytest.fixture
async def client(engine, session):
    from app.main import app
    from app.models import get_session as original_get_session

    async def override_get_session():
        yield session

    app.dependency_overrides[original_get_session] = override_get_session
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def sample_review(session):
    from app.models import Review
    import datetime
    review = Review(
        repo_full_name="kerberoskod/test-repo",
        pr_number=42,
        pr_title="Test PR",
        pr_author="testuser",
        status="completed",
        diff_summary="Fixed a bug",
        findings=[{"severity": "major", "category": "bug", "message": "Null pointer"}],
        total_comments=1,
        completed_at=datetime.datetime.now(datetime.UTC),
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)
    return review
