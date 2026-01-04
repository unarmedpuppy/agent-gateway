"""Tests for agent-core health endpoints."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "core"))

from main import app


@pytest.fixture
def client():
    """Create test client for core service."""
    return TestClient(app)


def test_health_endpoint(client):
    """Basic health check returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_v1_endpoint(client):
    """Detailed health check returns expected structure."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "local_ai_router" in data
    assert "agents" in data
    assert "version" in data


def test_list_agents(client):
    """Agents endpoint returns list of available agents."""
    response = client.get("/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert isinstance(data["agents"], list)
