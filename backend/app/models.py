import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, Integer, JSON, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repo_full_name = Column(String(255), nullable=False, index=True)
    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String(500), nullable=True)
    pr_author = Column(String(100), nullable=True)
    status = Column(String(20), default="pending")
    diff_summary = Column(Text, nullable=True)
    findings = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    total_comments = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    unique_repo_pr = ("repo_full_name", "pr_number")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    async with async_session() as session:
        yield session
