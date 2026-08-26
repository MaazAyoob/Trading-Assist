import pytest
from fastapi.testclient import TestClient
from app.main import app


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
