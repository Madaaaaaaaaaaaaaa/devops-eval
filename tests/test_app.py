import pytest

from app.main import app


@pytest.fixture
def client():
    return app.test_client()


def test_health_ok_with_db(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_visit_increments(client):
    a = client.post("/visit").get_json()["visits"]
    b = client.post("/visit").get_json()["visits"]
    assert b == a + 1


def test_metrics_exposes_counter(client):
    client.get("/health")
    body = client.get("/metrics").get_data(as_text=True)
    assert 'http_requests_total{code="200",endpoint="/health"}' in body
    assert "http_request_duration_seconds_bucket" in body
    assert "app_version_info" in body
