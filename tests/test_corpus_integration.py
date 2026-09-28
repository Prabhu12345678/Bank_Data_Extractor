import pytest
import os
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

CORPUS_DIRS = ["data/sample_documents", "data/financial_data_test_files"]

@pytest.fixture
def sample_files():
    # Returns a list of all files inside both sample_documents and the external test_files corpus recursively
    files = []
    for directory in CORPUS_DIRS:
        if os.path.exists(directory):
            for root, _, filenames in os.walk(directory):
                for f in filenames:
                    files.append(os.path.join(root, f))
    return files

@patch("src.api.routes.extractor")
def test_corpus_batch_processing(mock_extractor, sample_files):
    """
    Validates system stability by actively parsing all documents in the corpus.
    Ensures that ingestion and FastAPI correctly process dynamic real-world payloads
    without throwing 500 server errors, regardless of file type (prn, txt, csv).
    """
    if not sample_files:
        pytest.skip("No corpus files found to test.")

    # We mock the LLM extractor output so we aren't burning tokens during CI testing,
    # but we DO run the real Ingestion and real Validation agents against the payloads.
    mock_extractor.extract_from_json.return_value = json.dumps({
        "confidence_score": 0.95,
        "data": {
            "document_type": "Invoice",
            "entity_name": "Dynamic Vendor",
            "document_id": "PO-1002",
            "date": "09/20/2026",
            "total_amount": 1200.50, # Valid ERP total for PO-1002
            "line_items": [
                {"description": "Extracted Item", "quantity": 1, "unit_price": 1200.50, "total": 1200.50}
            ]
        }
    })

    file_success_count = 0
    for file_path in sample_files:
        filename = os.path.basename(file_path)

        # Open and load the file payload dynamically
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # Determine mime type for the integration route
        ext = filename.lower().split('.')[-1]
        mime_type = {
            "csv": "text/csv",
            "prn": "application/octet-stream",
            "txt": "text/plain"
        }.get(ext, "application/octet-stream")

        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )

        if filename.endswith(".xlsx"):
            assert response.status_code == 400, f"Expected 400 for {filename}"
            continue

        assert response.status_code == 200, f"Failed processing {filename}: {response.text}"
        payload = response.json()

        # Since we mocked a perfectly reconciled contract (PO-1002 / 1200.50)
        # all of these should technically pass through validation smoothly.
        assert payload["status"] == "APPROVED"
        assert len(payload["flags"]) == 0
        file_success_count += 1

    # Assert we processed at least 4 files from the corpus successfully
    assert file_success_count >= 4
