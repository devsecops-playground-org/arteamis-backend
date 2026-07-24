"""In-memory run store.

Deliberately not a database: this repository exists to exercise the delivery
pipeline, and a real datastore would only add setup that the pipeline does not test.
"""

from itertools import count

from app.models import Run, RunCreate, RunStatus


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[int, Run] = {}
        self._ids = count(1)

    def create(self, payload: RunCreate) -> Run:
        run = Run(id=next(self._ids), pipeline=payload.pipeline, triggered_by=payload.triggered_by)
        self._runs[run.id] = run
        return run

    def get(self, run_id: int) -> Run | None:
        return self._runs.get(run_id)

    def list(self, status: RunStatus | None = None) -> list[Run]:
        runs = list(self._runs.values())
        if status is not None:
            runs = [r for r in runs if r.status is status]
        return sorted(runs, key=lambda r: r.id)

    def advance(self, run_id: int, status: RunStatus) -> Run | None:
        run = self._runs.get(run_id)
        if run is None:
            return None
        if run.status in (RunStatus.SUCCEEDED, RunStatus.FAILED):
            raise ValueError(f"run {run_id} already finished as {run.status.value}")
        updated = run.model_copy(update={"status": status})
        self._runs[run_id] = updated
        return updated

    def clear(self) -> None:
        self._runs.clear()
