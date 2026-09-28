"""
Integration tests for edge cases and challenging documents from the real-world corpus.
Ensures the system gracefully handles bad data (empty files, corrupt PDFs, zero amounts),
flags anomalies appropriately, or rejects cleanly with a 400.
"""
import pytest
import os
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

# Location of edge case corpus files
EDGE_CASE_DIR = "data/financial_data_test_files/edge_cases"


def get_edge_case(filename: str):
    path = os.path.join(EDGE_CASE_DIR, filename)
    if not os.path.exists(path):
        pytest.skip(f"Corpus file {filename} not found.")

    with open(path, "rb") as f:
        file_bytes = f.read()

    ext = filename.lower().split('.')[-1]
    mime_type = {
        "csv": "text/csv",
        "pdf": "application/pdf",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "txt": "text/plain",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }.get(ext, "application/octet-stream")

    return filename, file_bytes, mime_type


class TestEdgeCaseIntegration:

    def test_empty_file(self):
        filename, file_bytes, mime_type = get_edge_case("empty_file.pdf")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        # Processed perfectly but likely low confidence because LLM sees no text
        assert response.status_code == 200
        payload = response.json()
        # Since it's empty, validation should flag it severely
        assert payload["status"] in ("REVIEW_REQUIRED", "ERROR")
        assert len(payload["flags"]) > 0

    def test_corrupt_pdf(self):
        filename, file_bytes, mime_type = get_edge_case("corrupt_pdf.pdf")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        # Even a corrupt PDF should not 500 error out (fallback parsed string is just "")
        assert response.status_code == 200

    def test_unsupported_format(self):
        filename, file_bytes, mime_type = get_edge_case("unsupported_format.xlsx")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        assert response.status_code == 400

    def test_zero_amount(self):
        filename, file_bytes, mime_type = get_edge_case("zero_amount.pdf")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        assert response.status_code == 200
        payload = response.json()
        assert "status" in payload

    def test_negative_amounts(self):
        filename, file_bytes, mime_type = get_edge_case("negative_amounts.pdf")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        assert response.status_code == 200
        payload = response.json()
        assert "status" in payload
        # Likely approved or rejected depending on what the LLM mock does with confidence

    def test_password_protected_stub(self):
        # We test that PyPDF2/pdfplumber does not crash process on encrypted PDFs
        filename, file_bytes, mime_type = get_edge_case("password_protected_stub.pdf")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        # Should gracefully return 200, but with empty text resulting in poor LLM extraction
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] in ("REVIEW_REQUIRED", "ERROR")

    def test_huge_line_items_pdf(self):
        filename, file_bytes, mime_type = get_edge_case("huge_line_items.pdf")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        assert response.status_code == 200

    def test_duplicate_invoices(self):
        filename_a, file_bytes_a, mime_type_a = get_edge_case("duplicate_invoice_number_a.pdf")
        filename_b, file_bytes_b, mime_type_b = get_edge_case("duplicate_invoice_number_b.pdf")

        # In a real DB-backed scenario, sending B after A would trigger a duplicate invoice anomaly flag.
        # Currently, our system is stateless in tests, so we just ensure they both parse successfully.
        resp_a = client.post(
            "/api/v1/process-document",
            files={"file": (filename_a, file_bytes_a, mime_type_a)}
        )
        assert resp_a.status_code == 200

        resp_b = client.post(
            "/api/v1/process-document",
            files={"file": (filename_b, file_bytes_b, mime_type_b)}
        )
        assert resp_b.status_code == 200

    def test_future_dated(self):
        filename, file_bytes, mime_type = get_edge_case("future_dated.pdf")
        response = client.post(
            "/api/v1/process-document",
            files={"file": (filename, file_bytes, mime_type)}
        )
        # System parses successfully
        assert response.status_code == 200
