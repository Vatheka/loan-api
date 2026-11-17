"""Run with: python train.py && pytest -v"""
import numpy as np
import pytest
from fastapi.testclient import TestClient

import main
from main import APPLICATIONS, app
from schemas import LoanFeatures

GOOD = {"amount_usd": 1500, "term_months": 12, "monthly_income_usd": 350.0, "previous_loans": 1, "late_payments": 0}


@pytest.fixture
def client():
    APPLICATIONS.clear()
    with TestClient(app) as c:  # "with" runs the lifespan, so the model is loaded
        yield c


def test_health_reports_model_version(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["model_version"]
    assert body["git_sha"] == main.GIT_SHA


def test_prediction_is_a_probability(client):
    body = client.post("/api/v1/predictions", json=GOOD).json()
    assert 0 <= body["default_probability"] <= 1
    assert body["risk_band"] in {"low", "medium", "high"}


def test_score_uses_default_probability_not_its_complement(monkeypatch):
    monkeypatch.setitem(main.ml, "features", list(GOOD))
    monkeypatch.setitem(main.ml, "predict_proba", lambda _: np.array([[0.08, 0.92]]))
    monkeypatch.setitem(main.ml, "version", "test")

    result = main.score(LoanFeatures(**GOOD))

    assert result.default_probability == 0.92
    assert result.risk_band == "high"


def test_api_key_protects_api_routes_but_not_health(client, monkeypatch):
    monkeypatch.setattr(main, "API_KEY", "test-api-key")

    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/applications").status_code == 401
    assert client.get(
        "/api/v1/applications",
        headers={"X-API-Key": "wrong-key"},
    ).status_code == 401
    assert client.get(
        "/api/v1/applications",
        headers={"X-API-Key": "test-api-key"},
    ).status_code == 200


def test_amount_above_limit_is_rejected(client):
    assert client.post("/api/v1/predictions", json={**GOOD, "amount_usd": 9000}).status_code == 422


def test_create_and_read_application(client):
    created = client.post("/api/v1/applications", json={**GOOD, "borrower_id": 1042})
    assert created.status_code == 201
    app_id = created.json()["id"]
    assert client.get(f"/api/v1/applications/{app_id}").json()["borrower_id"] == 1042


def test_missing_application_is_404(client):
    assert client.get("/api/v1/applications/99999").status_code == 404
