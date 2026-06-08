# Zephyr — AI Code Review

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/37_tests-passing-228B22?style=flat)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![Claude](https://img.shields.io/badge/Claude-Sonnet_4-9775FA?logo=anthropic&logoColor=white)

**Zephyr** is an AI-powered code review bot that automatically analyzes pull requests using Claude. When a PR is opened, Zephyr fetches the diff, runs it through an LLM, and posts structured findings (bugs, security issues, code quality, performance) directly as a PR comment.

---

## How It Works

```
GitHub PR opened
       │
       ▼
Webhook → FastAPI → Fetch diff
                     │
                     ▼
               Claude API (code review)
                     │
                     ▼
            Post findings as PR comment
                     │
                     ▼
            Dashboard (review history)
```

## Features

| Feature | Description |
|---|---|
| **Automated PR Review** | Triggers on `opened`, `synchronize`, `reopened` events |
| **Multi-Category Analysis** | Bugs, security, quality, performance, style |
| **Severity Levels** | Critical / Major / Minor with color-coded badges |
| **Inline Comments** | Posts a structured summary as a PR comment |
| **Review Dashboard** | View all reviews, filter by status, see findings |
| **Async Processing** | Webhook returns instantly, review runs in background |

## Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (async), aiosqlite |
| **AI** | Anthropic Claude Sonnet 4 |
| **Processing** | asyncio background tasks |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS |
| **GitHub** | GitHub App (webhooks, OAuth, API v3) |

## Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/kerberoskod/zephyr.git
cd zephyr
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
docker compose up -d
# Open http://localhost:5173
```

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in your keys
uvicorn app.main:app --reload  # http://localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev  # http://localhost:5173, proxies /api to :8000
```


## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key for code review |
| `GITHUB_APP_ID` | GitHub App ID |
| `GITHUB_PRIVATE_KEY` | GitHub App private key |
| `GITHUB_WEBHOOK_SECRET` | Webhook secret for signature verification |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret |
| `DATABASE_URL` | Database connection string |
| `JWT_SECRET` | JWT signing secret |
| `FRONTEND_URL` | Frontend URL for CORS |

## GitHub App Setup

1. Go to GitHub Settings → Developer Settings → GitHub Apps → New App
2. Set webhook URL: `https://your-domain.com/api/webhook`
3. Set permissions:
   - Pull requests: Read & Write
   - Checks: Read & Write
4. Subscribe to `Pull request` events
5. Install the app on your repositories

## License

MIT
