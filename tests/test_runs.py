import pytest

from app.config import Settings


def test_create_and_fetch_a_run(client):
    created = client.post("/api/runs", json={"pipeline": "nightly", "triggered_by": "nathan"})
    assert created.status_code == 201
    run = created.json()
    assert run["status"] == "queued"

    fetched = client.get(f"/api/runs/{run['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["pipeline"] == "nightly"


def test_missing_run_is_a_404(client):
    assert client.get("/api/runs/999").status_code == 404


def test_rejects_an_empty_pipeline_name(client):
    response = client.post("/api/runs", json={"pipeline": "", "triggered_by": "nathan"})
    assert response.status_code == 422


def test_listing_can_filter_by_status(client):
    first = client.post("/api/runs", json={"pipeline": "a", "triggered_by": "ci"}).json()
    client.post("/api/runs", json={"pipeline": "b", "triggered_by": "ci"})
    client.post(f"/api/runs/{first['id']}/status", params={"new_status": "running"})

    assert len(client.get("/api/runs").json()) == 2
    running = client.get("/api/runs", params={"run_status": "running"}).json()
    assert [r["pipeline"] for r in running] == ["a"]


def test_a_finished_run_cannot_be_advanced_again(client):
    run = client.post("/api/runs", json={"pipeline": "a", "triggered_by": "ci"}).json()
    client.post(f"/api/runs/{run['id']}/status", params={"new_status": "succeeded"})

    conflict = client.post(f"/api/runs/{run['id']}/status", params={"new_status": "running"})
    assert conflict.status_code == 409
    assert "already finished" in conflict.json()["detail"]


def test_advancing_an_unknown_run_is_a_404(client):
    assert client.post("/api/runs/42/status", params={"new_status": "running"}).status_code == 404


@pytest.mark.parametrize(
    ("env", "secret", "expected"),
    [
        ("development", "", []),
        ("production", "set", []),
        ("production", "", ["JWT_SECRET"]),
    ],
)
def test_production_requires_its_secrets(env, secret, expected):
    settings = Settings(app_env=env, jwt_secret=secret)
    assert settings.validate_for_production() == expected
