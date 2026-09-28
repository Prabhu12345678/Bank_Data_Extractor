import json
from src.validation.reconciliation import process_reconciliation

def test_reconciliation_math_failure():
    input_contract = json.dumps({
        "confidence_score": 0.95,
        "data": {
            "document_id": "PO-1001",
            "total_amount": 500.0,
            "line_items": [
                {"description": "Item 1", "total": 200.0},
                {"description": "Item 2", "total": 200.0}
            ]
        }
    })

    # 200 + 200 = 400. Total = 500. Should trigger math check failure.
    output_contract = process_reconciliation(input_contract)
    output_payload = json.loads(output_contract)

    assert output_payload["status"] == "REVIEW_REQUIRED"
    assert any("Math check failed" in flag for flag in output_payload["flags"])

def test_reconciliation_erp_mismatch():
    input_contract = json.dumps({
        "confidence_score": 0.95,
        "data": {
            "document_id": "PO-1001",
            "total_amount": 450.0, # ERP total for PO-1001 is 450.0
            "line_items": [
                {"description": "Item 1", "total": 250.0},
                {"description": "Item 2", "total": 200.0}
            ]
        }
    })

    output_contract = process_reconciliation(input_contract)
    output_payload = json.loads(output_contract)

    assert output_payload["status"] == "APPROVED"
    assert len(output_payload["flags"]) == 0

def test_reconciliation_upstream_error():
    input_contract = json.dumps({
        "error": "LLM timed out"
    })

    output_contract = process_reconciliation(input_contract)
    output_payload = json.loads(output_contract)

    assert output_payload["status"] == "ERROR"
    assert "LLM timed out" in output_payload["flags"]
