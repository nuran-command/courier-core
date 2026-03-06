# Courier Core — Smart Assignment Engine (Member 1: Backend/Architect)

> **Jana Courier Hackathon** | Member 1 Role: Infrastructure, API, and Data Models  

##  Project Vision
This repository provides the high-performance infrastructure for the **Jana Courier Smart Assignment Engine**. It is designed to minimize late deliveries, maximize fleet utilization, and provide a secure, auditable foundation for Member 2's optimization algorithms.

###  Architect's Highlights (Member 1)
- **Road-Aware Logistics**: Integrated **OSRM** for real-world road network distances and ETA (Travel Duration).
- **Industrial Database**: Powered by **PostgreSQL** for persistence and **SQLAlchemy 2.0** for ORM mapping.
- **SLA Dashboard**: Built-in `/analytics/sla` endpoint to monitor operational productivity and priority service levels.
- **Architect's Shield**: Secured endpoints using **API Key Authentication** (`X-API-KEY`).
- **Dual-Engine Persistence**: Optimized for both **SQLite** (instant zero-config demo) and **PostgreSQL** (production-grade capacity).
- **Resilience**: Smart database retry loops to handle Docker startup warm-up times.
- **ML-Ready Data**: Captures and logs every assignment with metadata (priorities, deadlines, weights) for future model training.

---

##  Tech Stack
- **Framework**: FastAPI (Asynchronous Python)
- **Validation**: Pydantic V2 (Strict typing)
- **Database**: PostgreSQL 15 + SQLAlchemy
- **Containerization**: Docker & Docker Compose
- **Geo-Routing**: OSRM (Open Source Routing Machine)

---

##  Quickstart (The Fast Way)

The recommended way to run the project is using **Docker**, as it automatically sets up the PostgreSQL database and the API network.

```bash
# 1. Build and start everything
docker compose up --build -d

# 2. Run the simulation script to see the brain in action
python simulate.py
```

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Analytics**: [http://localhost:8000/analytics/sla](http://localhost:8000/analytics/sla)
- **API Key**: `JANA_COURIER_2026` (Required for Protected Endpoints)

---

##  API Endpoints

| Method | Path              | Protected | Description |
|--------|-------------------|-----------|-------------|
| GET    | `/`               |  No     | Health Check & Service Info |
| POST   | `/assign`         |  Yes    | Run Smart Assignment Engine |
| GET    | `/history`        |  Yes    | Audit Log of Assignment History |
| GET    | `/analytics/sla`  |  No     | Operational & Efficiency Stats |

---

##  Project Structure

```
courier-core/
├── app/
│   ├── api/
│   │   ├── routes.py       ← Core API Endpoints (Protected)
│   │   └── analytics.py    ← SLA & Efficiency Analytics
│   ├── core/
│   │   ├── geo.py           ← OSRM Road Distance & ETA Logic
│   │   ├── filters.py       ← Courier Capacity & Status Guards
│   │   └── assignment.py    ← Bridge for Member 2's Optimization Logic
│   ├── models.py           ← Strict Data Contracts (Pydantic V2)
│   ├── db.py               ← PostgreSQL Engine & Resilience Logic
│   └── crud.py             ← Database Access Layer
├── tests/                  ← Pytest Suite (Integration & Unit)
├── simulate.py             ← Full End-to-End Simulation Client
├── Dockerfile              ← Production-ready image setup
├── docker-compose.yml      ← Orchestrated Fleet (DB + API)
└── .env                    ← Environment Configuration
```

---

##  Testing

```bash
# Set environment to testing and run pytest
export TESTING=1
pytest
```

---
