

## Project Name

Commerce AI Platform

---

## Objective

This repository is for a Commerce AI Platform that helps businesses convert Instagram Reel content into structured product data and use that data to support customer conversations such as pricing, availability, and booking over WhatsApp.

The product should eventually be able to:

1. read Instagram Reel content
2. obtain or accept transcript text
3. convert transcript text into structured product information
4. store product information
5. support downstream messaging workflows for customer inquiries
6. help answer WhatsApp questions related to pricing, booking, and product details

---

## Current Tech Stack

### Backend
- Python
- FastAPI
- backend code lives in `apps/api`

### Frontend
- React
- Vite
- frontend code lives in `apps/web`

### Testing
- backend tests live in top-level `tests/`

---

## Repository Structure

```text
COMMERCE-AI-PLATFORM/
├── apps/
│   ├── api/
│   │   ├── core/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── tests/
│   │   ├── __init__.py
│   │   └── main.py
│   └── web/
├── scripts/
├── tests/
├── .env
├── pyproject.toml
├── README.md
└── CLAUDE.md