"""
app/main.py — FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.db import create_tables

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup / shutdown logic."""
    # Create DB tables on first run (SQLite auto-creates the file)
    create_tables()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Smart Assignment Engine for Jana Courier — minimises late deliveries "
        "by solving a Capacitated Vehicle Routing Problem (CVRP) with "
        "deadline urgency, order priority, and courier load constraints."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow cross-origin requests (useful for the frontend teammate)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
