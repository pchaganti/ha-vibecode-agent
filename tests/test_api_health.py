"""Smoke tests for API endpoints using FastAPI TestClient."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import os

os.environ.setdefault("HA_TOKEN", "test-token")
os.environ.setdefault("HA_URL", "http://localhost:8123")
os.environ.setdefault("CONFIG_PATH", "/tmp/test-config")

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint (no auth required)."""

    def test_health_returns_200(self):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_has_version(self):
        response = client.get("/api/health")
        data = response.json()
        assert "version" in data
        assert "status" in data

    def test_health_status_healthy(self):
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthRequired:
    """Test that endpoints require authentication."""

    def test_entities_requires_auth(self):
        response = client.get("/api/entities/list")
        assert response.status_code in (401, 403)

    def test_files_requires_auth(self):
        response = client.get("/api/files/list")
        assert response.status_code in (401, 403)

    def test_automations_requires_auth(self):
        response = client.get("/api/automations/list")
        assert response.status_code in (401, 403)

    def test_system_requires_auth(self):
        response = client.get("/api/system/config")
        assert response.status_code in (401, 403)


class TestDocsEndpoints:
    """Test that API docs are accessible."""

    def test_swagger_ui(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc(self):
        response = client.get("/redoc")
        assert response.status_code == 200
