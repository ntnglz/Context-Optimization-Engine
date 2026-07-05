"""Tests HTTP API COE — smoke con TestClient."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from coe.http.app import app

SAMPLE_BLOCKS = [
    {"id": "A", "content": "Empresa: ACME\nCliente: Globex"},
    {"id": "B", "content": "Empresa: ACME\nPresupuesto: 50k"},
    {"id": "C", "content": "Empresa: ACME\nCliente: Globex"},
]

PAYLOAD = {
    "blocks": SAMPLE_BLOCKS,
    "levels": [1],
    "locale": "en",
}


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHttpHealth:
    def test_health(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestHttpOptimize:
    def test_optimize_returns_prose_and_metrics(self, client: TestClient):
        response = client.post("/optimize", json=PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "text" in data
        assert "metrics" in data
        assert data["metrics"]["original_tokens"] > 0
        assert "ACME" in data["text"]

    def test_optimize_empty_blocks_400(self, client: TestClient):
        response = client.post("/optimize", json={"blocks": [], "levels": [1]})
        assert response.status_code == 422 or response.status_code == 400


class TestHttpEstimate:
    def test_estimate_returns_metrics_only(self, client: TestClient):
        response = client.post("/estimate", json=PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "text" not in data
        assert data["original_tokens"] > 0
        assert "tokens_saved" in data
        assert "truncated" in data

    def test_estimate_with_max_context_tokens(self, client: TestClient):
        response = client.post(
            "/estimate",
            json={**PAYLOAD, "max_context_tokens": 500},
        )
        assert response.status_code == 200
        assert response.json()["optimized_tokens"] > 0
