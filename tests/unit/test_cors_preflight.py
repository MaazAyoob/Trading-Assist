import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import Settings


def test_cors_preflight_production_vercel():
    client = TestClient(app)

    # 1. Test OPTIONS preflight from Vercel production frontend
    headers = {
        "Origin": "https://trading-assist-website.vercel.app",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/api/v1/scalp?symbol=BTCUSDT", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://trading-assist-website.vercel.app"

    # 2. Test actual GET request from Vercel production frontend
    headers_get = {
        "Origin": "https://trading-assist-website.vercel.app",
    }
    response_get = client.get("/", headers=headers_get)
    assert response_get.status_code == 200
    assert response_get.headers.get("access-control-allow-origin") == "https://trading-assist-website.vercel.app"


def test_cors_preflight_vercel_preview_domain():
    client = TestClient(app)

    headers = {
        "Origin": "https://trading-assist-preview-123.vercel.app",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/scalp?symbol=BTCUSDT", headers=headers)
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "https://trading-assist-preview-123.vercel.app"


def test_cors_on_404_error():
    client = TestClient(app)
    headers = {"Origin": "https://trading-assist-website.vercel.app"}
    response = client.get("/api/v1/non_existent_route", headers=headers)
    assert response.status_code == 404
    assert response.headers.get("access-control-allow-origin") == "https://trading-assist-website.vercel.app"


def test_cors_on_500_error():
    client = TestClient(app, raise_server_exceptions=False)

    @app.get("/test-unhandled-crash-cors")
    def crash_endpoint():
        raise RuntimeError("Crash for testing CORS on 500")

    headers = {"Origin": "https://trading-assist-website.vercel.app"}
    response = client.get("/test-unhandled-crash-cors", headers=headers)
    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == "https://trading-assist-website.vercel.app"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_disallowed_origin():
    client = TestClient(app)
    headers = {"Origin": "https://malicious-site.com"}
    response = client.get("/", headers=headers)
    assert response.headers.get("access-control-allow-origin") is None


def test_backend_cors_origins_env_parsing():
    # Test comma-separated string
    os.environ["BACKEND_CORS_ORIGINS"] = "https://trading-assist-website.vercel.app,http://localhost:3000"
    s1 = Settings()
    assert s1.BACKEND_CORS_ORIGINS == [
        "https://trading-assist-website.vercel.app",
        "http://localhost:3000",
    ]

    # Test single plain string
    os.environ["BACKEND_CORS_ORIGINS"] = "https://trading-assist-website.vercel.app"
    s2 = Settings()
    assert s2.BACKEND_CORS_ORIGINS == ["https://trading-assist-website.vercel.app"]

    # Test JSON string
    os.environ["BACKEND_CORS_ORIGINS"] = '["https://trading-assist-website.vercel.app"]'
    s3 = Settings()
    assert s3.BACKEND_CORS_ORIGINS == ["https://trading-assist-website.vercel.app"]

    # Clean up env
    del os.environ["BACKEND_CORS_ORIGINS"]
