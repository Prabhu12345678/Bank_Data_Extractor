import pytest
import json
from src.ingestion.parser import process_ingestion

def test_ingestion_txt_file():
    file_bytes = b"Sample text document content"
    result_str = process_ingestion(file_bytes, "sample.txt", "text/plain")
    result_payload = json.loads(result_str)

    assert "document_text" in result_payload
    assert result_payload["document_text"].strip() == "Sample text document content"
    assert result_payload["metadata"]["filename"] == "sample.txt"
    assert result_payload["metadata"]["type"] == "text/plain"

def test_ingestion_prn_file():
    file_bytes = b"      PO-1001     450.00"
    result_str = process_ingestion(file_bytes, "report.prn", "application/octet-stream")
    result_payload = json.loads(result_str)

    assert "document_text" in result_payload
    assert result_payload["document_text"].strip() == "PO-1001     450.00"
    assert result_payload["metadata"]["filename"] == "report.prn"
    assert result_payload["metadata"]["type"] == "application/octet-stream"

def test_ingestion_empty_file():
    file_bytes = b""
    result_str = process_ingestion(file_bytes, "empty.txt", "text/plain")
    result_payload = json.loads(result_str)

    # Still parses, but returns empty text
    assert "document_text" in result_payload
    assert result_payload["document_text"].strip() == ""

def test_ingestion_decode_fallback():
    # Provide explicitly non-utf-8 bytes that aren't easily decodable
    file_bytes = b"\xff\xfe\x00\x00"
    result_str = process_ingestion(file_bytes, "weird.prn", "application/octet-stream")
    result_payload = json.loads(result_str)

    # Should fallback to ignore or replace but shouldn't crash
    assert "document_text" in result_payload
