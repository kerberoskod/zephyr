import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Review, init_db, get_session
from app.schemas import ReviewListResponse, ReviewResponse
from app.webhook import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Zephyr Code Review", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router, prefix="/api")


@app.get("/api/reviews", response_model=ReviewListResponse)
async def list_reviews(
    page: int = 1,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
):
    offset = (page - 1) * limit
    total_q = select(func.count(Review.id))
    total = (await session.execute(total_q)).scalar() or 0

    q = select(Review).order_by(Review.created_at.desc()).offset(offset).limit(limit)
    rows = (await session.execute(q)).scalars().all()

    return ReviewListResponse(
        reviews=[ReviewResponse.model_validate(r) for r in rows],
        total=total,
    )


@app.get("/api/reviews/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: str, session: AsyncSession = Depends(get_session)):
    review = await session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse.model_validate(review)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "zephyr"}
