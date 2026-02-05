"""Tests for main FastAPI application."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Root endpoint should return app info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_endpoint():
    """Health check should return healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_metrics_endpoint():
    """Metrics endpoint should exist (even if not implemented)."""
    response = client.get("/metrics")
    assert response.status_code in [200, 501]  # 501 = Not Implemented yet
