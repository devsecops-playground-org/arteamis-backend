"""Application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from app import __version__
from app.config import get_settings
from app.models import Health, Run, RunCreate, RunStatus
from app.store import RunStore

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Refuse to serve traffic if production is missing a required secret."""
    missing = get_settings().validate_for_production()
    if missing:
        raise RuntimeError(f"missing required production secrets: {', '.join(missing)}")
    yield


app = FastAPI(title="Arteamis API", version=__version__, lifespan=lifespan)
store = RunStore()


@app.get("/health", response_model=Health, tags=["ops"])
def health() -> Health:
    """Liveness probe. The container healthcheck and the deploy gate both read this."""
    settings = get_settings()
    return Health(status="ok", environment=settings.app_env, version=__version__)


@app.post("/api/runs", response_model=Run, status_code=status.HTTP_201_CREATED, tags=["runs"])
def create_run(payload: RunCreate) -> Run:
    return store.create(payload)


@app.get("/api/runs", response_model=list[Run], tags=["runs"])
def list_runs(run_status: RunStatus | None = None) -> list[Run]:
    return store.list(run_status)


@app.get("/api/runs/{run_id}", response_model=Run, tags=["runs"])
def get_run(run_id: int) -> Run:
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return run


@app.post("/api/runs/{run_id}/status", response_model=Run, tags=["runs"])
def advance_run(run_id: int, new_status: RunStatus) -> Run:
    try:
        run = store.advance(run_id, new_status)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return run
