# Commerce AI Platform

A platform that converts Instagram Reel content into structured product data and powers customer conversations over WhatsApp.

## Overview

Businesses point the platform at Instagram Reels. The platform extracts transcripts, turns them into structured product records, and then uses that data to answer customer questions about pricing, availability, and booking via WhatsApp.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic |
| Frontend | React 19, Vite |
| Testing | pytest, httpx |

## Repository Structure

```
COMMERCE-AI-PLATFORM/
├── apps/
│   ├── api/               # FastAPI backend
│   │   ├── core/          # Config and logging
│   │   ├── domain/        # Domain models
│   │   ├── infrastructure/# DB and repositories
│   │   ├── routes/        # API route handlers
│   │   ├── services/      # Business logic
│   │   └── main.py        # App entrypoint
│   └── web/               # React frontend
├── scripts/               # Dev/ops helper scripts
├── tests/                 # Backend integration tests
├── pyproject.toml
└── CLAUDE.md
```

## Getting Started

### Prerequisites

- Python 3.12 (`brew install python@3.12`)
- Node.js 18+

### Backend

```bash
# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies (including dev extras)
pip install -e ".[dev]"

# Run the API server
uvicorn apps.api.main:app --reload
```

API is available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

Frontend is available at `http://localhost:5173`.

### Running Tests

```bash
# From repo root with venv active
pytest
```