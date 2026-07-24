"""API schema."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class RunCreate(BaseModel):
    pipeline: str = Field(min_length=1, max_length=120)
    triggered_by: str = Field(min_length=1, max_length=120)


class Run(BaseModel):
    id: int
    pipeline: str
    triggered_by: str
    status: RunStatus = RunStatus.QUEUED
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Health(BaseModel):
    status: str
    environment: str
    version: str
