"""ha_hacs_install_repository must accept JSON body like the MCP client sends."""
import os
from pathlib import Path
from unittest.mock import patch

import pytest

HACS_API = Path(__file__).resolve().parents[1] / "app" / "api" / "hacs.py"


def test_endpoint_declares_repository_as_json_body():
    """Bare `repository: str` made FastAPI require a query param; MCP posts JSON."""
    source = HACS_API.read_text(encoding="utf-8")
    assert "repository: Optional[str] = Body(" in source
    assert "async def install_hacs_repository(repository: str" not in source


os.environ.setdefault("HA_TOKEN", "test-token")
os.environ.setdefault("HA_URL", "http://localhost:8123")
os.environ.setdefault("CONFIG_PATH", "/tmp/test-config")

try:
    from fastapi.testclient import TestClient

    from app.auth import verify_token
    from app.main import app
except Exception:  # pragma: no cover - local env without agent deps
    TestClient = None
    app = None
    verify_token = None


@pytest.mark.skipif(TestClient is None, reason="agent runtime dependencies are not installed")
class TestHacsInstallRepositoryParams:
    """MCP posts JSON body; FastAPI used to require query params and 422."""

    def _client_with_auth(self):
        app.dependency_overrides[verify_token] = lambda: "test"
        return TestClient(app)

    def teardown_method(self):
        app.dependency_overrides.clear()

    def test_json_body_is_not_query_validation_error(self):
        client = self._client_with_auth()
        with patch("app.api.hacs.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            response = client.post(
                "/api/hacs/install_repository",
                json={
                    "repository": "Vortitron/HAFamilyLink",
                    "category": "integration",
                },
            )

        assert response.status_code != 422
        payload = response.json()
        loc = str(payload)
        assert '"loc":["query","repository"]' not in loc.replace(" ", "")
        assert response.status_code == 400
        assert "HACS is not installed" in loc

    def test_legacy_query_string_still_accepted(self):
        client = self._client_with_auth()
        with patch("app.api.hacs.Path") as mock_path:
            mock_path.return_value.exists.return_value = False
            response = client.post(
                "/api/hacs/install_repository",
                params={
                    "repository": "Vortitron/HAFamilyLink",
                    "category": "integration",
                },
            )

        assert response.status_code == 400
        assert "HACS is not installed" in response.text
