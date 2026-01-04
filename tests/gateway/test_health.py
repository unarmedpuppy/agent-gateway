"""Tests for agent-gateway health endpoints."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add gateway to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "gateway"))

from main import app


@pytest.fixture
def client():
    """Create test client for gateway service."""
    return TestClient(app)


def test_health_endpoint(client):
    """Basic health check returns status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "adapters" in data


def test_list_adapters(client):
    """Adapters endpoint returns list of adapters."""
    response = client.get("/adapters")
    assert response.status_code == 200
    data = response.json()
    assert "adapters" in data
    assert isinstance(data["adapters"], list)
