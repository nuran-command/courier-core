#  Jana Courier — Smart Assignment Engine (MVP)

> **Challenge**: Optimize logistics to minimize late deliveries, balance fleet load, and ensure high operational efficiency.

This repository contains the **complete implementation** of the Jana Courier platform, featuring a high-performance **FastAPI Backend** and a premium **React-based Command Center**.

---

##  Architectural Overview

###  Backend (Architect Core)
Designed for **Proprietary Intelligence** and **Operational Reliability**:
- **Smart Heuristic Solver (Member 1 Proprietary V1)**: Implements Priority-First sorting and **Earliest Deadline First (EDF)** allocation.
- **Load Balancing**: Advanced logic to prevent courier overload by distributing assignments based on minimal utilization delta.
- **Geo-Routing Intelligence**: Integrated with **OSRM** for real-world road network distances and ETA (Travel Duration) calculations.
- **SLA Audit Layer**: Real-time analytics engine (`/analytics/sla`) monitoring fleet health and service level compliance.
- **Dual-Engine Persistence**: Production-grade support for **PostgreSQL** with a simplified **SQLite** mode for instant zero-config demos.
- **Security**: Endpoint hardening via **API Key Authentication** (`X-API-KEY: JANA_COURIER_2026`).

###  Frontend (Mission Control)
A high-end **Command Center** designed for dispatchers:
- **Real-time Map Intelligence**: Leaflet-powered map with **Pulsing VIP Markers**, interactive route tooltips, and a network legend.
- **Neural Activity Feed**: A live "System Audit" log showing backend events (OSRM fetches, Solver engaging, DB commits).
- **KPI Monitoring**: Dynamic dashboards tracking **Fleet Balance %**, **Avg Efficiency**, and **SLA Status**.
- **Management Tools**: Dedicated modules for **Fleet Assets** (Couriers) and **Live Bundles** (Order Queue) with full detail views.
- **VRP Control**: Manual trigger for the neural assignment engine with 1-click optimization.

---

##  Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic V2, PostgreSQL 15 |
| **Frontend** | React, Vite, Tailwind CSS, Leaflet, Framer Motion, Lucide React, Axios |
| **Geo** | OSRM (Open Source Routing Machine) |
| **DevOps** | Docker, Docker Compose, Pytest |

---

##  Quickstart (Launch Engine)

### 1. Backend Setup
The recommended way is using **Docker** to handle all dependencies:
```bash
# Start the Backend & Database
docker compose up --build -d
```
*   **Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
*   **System Key**: `JANA_COURIER_2026`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*   **Dashboard URL**: [http://localhost:3000](http://localhost:3000)
*   **Login**: The dashboard is secured. Use the system key above to enter.

---

##  Evaluation Criteria Alignment

| Criterion | Implementation in Jana Courier |
|---|---|
| **Operational Effect (3.1)** | Decreased late deliveries via **EDF Priority Logic** and **Fleet Load Balancing**. |
| **Financial Effect (3.2)** | Enhanced efficiency via **OSRM Travel Duration** optimization (reducing fuel/time). |
| **Technological Effect (3.3)** | Built-in **Proprietary Heuristic Core** and **ML-Ready Data Pipeline** for future scaling. |

---

##  Project Structure

```
courier-core/
├── app/                  ← Backend Core Logic
│   ├── api/              ← Protected Endpoints & Analytics
│   ├── core/             ← Proprietary Solver & Geo logic
│   ├── models.py         ← Pydantic V2 Data Contracts
│   └── db.py             ← Resilience & DB Connection Logic
├── frontend/             ← React Dashboard (Vite)
│   ├── src/App.jsx       ← Mission Control Component
│   └── src/index.css     ← Premium Design System
├── tests/                ← Pytest Integration Suite
├── Dockerfile            ← Production-ready image setup
└── docker-compose.yml    ← Fleet Orchestration (API + DB)
```

---

##  Testing Verification
Every component is tested for reliability:
```bash
export TESTING=1
pytest
```
*Manual validation:* Use the **'Trigger VRP SmartAssign'** button in the dashboard to see the neural solver process real-time nodes.

---
**Status: Pitch Ready | Neural Engine v4.2 (Optimized)**
