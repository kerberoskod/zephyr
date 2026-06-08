import pytest


class TestListReviews:
    async def test_empty_list(self, client):
        resp = await client.get("/api/reviews")
        assert resp.status_code == 200
        body = resp.json()
        assert body["reviews"] == []
        assert body["total"] == 0

    async def test_with_reviews(self, client, sample_review):
        resp = await client.get("/api/reviews")
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["reviews"]) == 1
        r = body["reviews"][0]
        assert r["repo_full_name"] == "kerberoskod/test-repo"
        assert r["pr_number"] == 42
        assert r["status"] == "completed"

    async def test_pagination(self, client, session):
        from app.models import Review

        for i in range(5):
            session.add(Review(repo_full_name="repo/a", pr_number=100 + i, status="pending"))
        await session.commit()

        resp = await client.get("/api/reviews?page=1&limit=2")
        body = resp.json()
        assert len(body["reviews"]) == 2
        assert body["total"] == 5

    async def test_negative_limit(self, client):
        resp = await client.get("/api/reviews?limit=-1")
        assert resp.status_code == 422


class TestGetReview:
    async def test_found(self, client, sample_review):
        resp = await client.get(f"/api/reviews/{sample_review.id}")
        assert resp.status_code == 200
        assert resp.json()["pr_number"] == 42

    async def test_not_found(self, client):
        resp = await client.get("/api/reviews/nonexistent-id")
        assert resp.status_code == 404


class TestHealth:
    async def test_health_ok(self, client):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "zephyr"
