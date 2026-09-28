import json
from src.config.settings import settings

MOCK_ERP_DB = {
    "PO-1001": {"expected_total": 450.00, "vendor": "Acme Corp"},
    "PO-1002": {"expected_total": 1200.50, "vendor": "TechSupply Inc."}
}

def process_reconciliation(input_json_str: str) -> str:
    """
    Validation Agent:
    Input Contract: JSON string containing extracted data schema (confidence_score, data)
    Output Contract: JSON string containing validation results (status, flags, extracted_data)
    """
    try:
        payload = json.loads(input_json_str)

        # Check if upstream returned an error
        if "error" in payload:
            return json.dumps({
                "status": "ERROR",
                "flags": [payload["error"]],
                "extracted_data": {}
            })

        confidence_score = payload.get("confidence_score", 0.0)
        data = payload.get("data", {})

        is_valid = True
        flags = []

        # 1. Check AI confidence score vs threshold
        if confidence_score < settings.confidence_threshold:
            is_valid = False
            flags.append(f"Low confidence score: {confidence_score}")

        # 2. Check Math (Sum of line items + tax == total_amount)
        line_items = data.get("line_items", [])
        total_amount = data.get("total_amount")
        total_tax_amount = data.get("total_tax_amount", 0.0)

        if line_items and total_amount is not None:
            calc_total = sum(item.get("total", 0.0) for item in line_items) + total_tax_amount
            if abs(calc_total - total_amount) > 0.01:
                is_valid = False
                flags.append(f"Math check failed: line items sum ({calc_total - total_tax_amount}) + tax ({total_tax_amount}) != total {total_amount}")

        # 3. ERP Matching (Simulated)
        document_id = data.get("document_id")
        if document_id in MOCK_ERP_DB:
            erp_record = MOCK_ERP_DB[document_id]
            if total_amount is not None and abs(erp_record["expected_total"] - total_amount) > 0.01:
                is_valid = False
                flags.append(f"ERP mismatch: expected {erp_record['expected_total']}, got {total_amount}")

        output_contract = {
            "status": "APPROVED" if is_valid else "REVIEW_REQUIRED",
            "flags": flags,
            "extracted_data": payload
        }

        return json.dumps(output_contract)

    except Exception as e:
        return json.dumps({
            "status": "ERROR",
            "flags": [f"Reconciliation agent error: {str(e)}"],
            "extracted_data": {}
        })
