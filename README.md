# Courier Core — Smart Assignment Engine (Member 1: Backend/Architect)

> **Jana Courier Hackathon** | Member 1 Role: Infrastructure, API, and Data Models  
> Deadline: 10 March 2026

## Overview

This project implements the core architecture and infrastructure for the Jana Courier Smart Assignment Engine. As Member 1 (Backend/Architect), this codebase provides:

- **Robust API**: Built with FastAPI, including validation and auto-documentation.
- **Strict Data Contracts**: Pydantic models for Orders and Couriers.
- **Persistence**: SQLite (via SQLAlchemy) for logging assignment operations.
- **Courier Filtering**: Business logic to ensure only available and capable couriers are passed to the assignment logic.
- **Geo-Utilities**: Haversine distance calculations for location-based logic.
- **Development Tools**: Simulation scripts, unit/integration tests, and Docker support.

*Note: The complex optimization "Brain" (OR-Tools/VRP) is intended to be implemented by Member 2 in `app/core/assignment.py`.*

---

## Quickstart (local)

```bash
# 1. Create virtual environment
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy env template
cp .env.example .env   # or edit .env directly

# 4. Start the server
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Quickstart (Docker)

```bash
docker compose up --build
```

---

## API Endpoints

| Method | Path       | Description                              |
|--------|------------|------------------------------------------|
| GET    | `/`        | Health check                             |
| POST   | `/assign`  | Process assignment (Member 1 Filter + Placeholder Solve) |
| GET    | `/history` | View assignment history log              |

---

## Project Structure (Member 1 Focus)

```
courier-core/
├── app/
│   ├── main.py          ← FastAPI entry point
│   ├── models.py        ← Pydantic: Order, Courier, Request/Response
│   ├── config.py        ← Settings & Environment
│   ├── db.py            ← SQLite Database Setup
│   ├── crud.py          ← Database Operations
│   ├── api/
│   │   └── routes.py    ← API Endpoint Definitions
│   └── core/
│       ├── geo.py        ← Geographic Math (Haversine)
│       ├── filters.py    ← Courier Capacity & Status Filtering
│       └── assignment.py ← Assignment Logic (Skeleton/Placeholder)
├── tests/
│   ├── test_models.py
│   ├── test_geo.py
│   └── test_assign.py
├── simulate.py          ← API Stress Test/Simulation
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```