import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_invalid_file_type():
    file_data = b"dummy content"
    response = client.post(
        "/api/v1/process-document",
        files={"file": ("test.exe", file_data, "application/x-msdownload")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

# Positive Integration Test: Full pipeline mock
@patch("src.api.routes.extractor")
def test_full_pipeline_success(mock_extractor):
    # Setup mock extractor to bypass actual LLM parsing during testing
    # Expects extraction JSON contract output which gets passed to reconciliation
    mock_extractor.extract_from_json.return_value = json.dumps({
        "confidence_score": 0.99,
        "data": {
            "document_type": "Invoice",
            "entity_name": "ACME CORP",
            "document_id": "PO-1001",
            "date": "09/20/2026",
            "total_amount": 450.00,
            "line_items": [
                {"description": "Item 1", "quantity": 1, "unit_price": 250.0, "total": 250.0},
                {"description": "Item 2", "quantity": 1, "unit_price": 200.0, "total": 200.0}
            ]
        }
    })

    file_data = b"SAMPLE INVOICE PO-1001 TOTAL 450.00"
    response = client.post(
        "/api/v1/process-document",
        files={"file": ("invoice.txt", file_data, "text/plain")}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "APPROVED"
    assert len(payload["flags"]) == 0
    assert payload["extracted_data"]["data"]["document_id"] == "PO-1001"

# Negative Integration Test: Math anomaly triggers flag
@patch("src.api.routes.extractor")
def test_full_pipeline_anomaly_detected(mock_extractor):
    mock_extractor.extract_from_json.return_value = json.dumps({
        "confidence_score": 0.99,
        "data": {
            "document_type": "Invoice",
            "entity_name": "ACME CORP",
            "document_id": "PO-1002",
            "date": "09/20/2026",
            "total_amount": 2000.00, # Math check failure (1000 + 1000 = 2000, ERP wants 1200.50)
            "line_items": [
                {"description": "Item 1", "quantity": 1, "unit_price": 1000.0, "total": 1000.0},
                {"description": "Item 2", "quantity": 1, "unit_price": 1000.0, "total": 1000.0}
            ]
        }
    })

    file_data = b"SAMPLE INVOICE PO-1002 TOTAL 2000.00"
    response = client.post(
        "/api/v1/process-document",
        files={"file": ("anomaly_invoice.txt", file_data, "text/plain")}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "REVIEW_REQUIRED"
    assert any("ERP mismatch" in flag for flag in payload["flags"])

# Edge Case: Confidence Score Too Low
@patch("src.api.routes.extractor")
def test_low_confidence_score(mock_extractor):
    mock_extractor.extract_from_json.return_value = json.dumps({
        "confidence_score": 0.50, # Way below 0.85 threshold
        "data": {
            "document_id": "PO-1001",
            "total_amount": 450.00,
            "line_items": []
        }
    })

    file_data = b"Blurry Text"
    response = client.post(
        "/api/v1/process-document",
        files={"file": ("blurry.txt", file_data, "text/plain")}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "REVIEW_REQUIRED"
    assert any("Low confidence score" in flag for flag in payload["flags"])

# Edge Case: Extraction Agent failed outright
@patch("src.api.routes.extractor")
def test_extraction_hard_failure(mock_extractor):
    mock_extractor.extract_from_json.return_value = json.dumps({
        "error": "LLM Connection Reset"
    })

    file_data = b"Does not matter, LLM is failing"
    response = client.post(
        "/api/v1/process-document",
        files={"file": ("crash.txt", file_data, "text/plain")}
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ERROR"
    assert payload["flags"] == ["LLM Connection Reset"]
