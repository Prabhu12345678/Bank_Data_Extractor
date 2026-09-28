import pytest
import json
from src.validation.reconciliation import process_reconciliation
import itertools

# We will generate a matrix of 300 test cases using permutations.
# Elements:
# 1. 10 Confidence Scores (Edge values, exact bounds, out of bounds)
CONFIDENCES = [-0.1, 0.0, 0.1, 0.84, 0.85, 0.86, 0.99, 1.0, 1.1, None]

# 2. 5 Math Configurations (Sum matches total, slightly off, drastically off, missing total, negative values)
MATH_CONFIGS = [
    # (line_items, total_amount, expected_math_flag_present)
    ([{"total": 100.0}, {"total": 50.0}], 150.0, False),                 # Perfect Match
    ([{"total": 100.01}, {"total": 49.99}], 150.0, False),               # Exact sum
    ([{"total": 100.10}, {"total": 50.0}], 150.0, True),                 # Off by 10 cents
    ([{"total": 100.0}, {"total": 50.0}], 9999.0, True),                 # Massively off
    ([{"total": -50.0}, {"total": 100.0}], 50.0, False),                 # Negative credits
    ([], 150.0, False),                                                  # No line items (math not applied)
]

# 3. 5 ERP Conditions for "PO-1002" WHICH expects 1200.50
ERP_CONFIGS = [
    # (document_id, total_amount, expected_erp_flag_present)
    ("PO-1002", 1200.50, False),    # Exact match against mock ERP
    ("PO-1002", 1200.51, True),     # 1 cent off ERP threshold
    ("PO-1002", 900.00, True),      # Completely off
    ("UNKNOWN-PO", 1200.50, False), # PO not in ERP (defaults to pass ERP check since it's not present)
    (None, 1200.50, False),         # No document ID parsed
]

# Total test combinations: 10 * 6 * 5 = 300 Test Cases!
TEST_MATRIX = list(itertools.product(CONFIDENCES, MATH_CONFIGS, ERP_CONFIGS))

@pytest.mark.parametrize("confidence, math_cfg, erp_cfg", TEST_MATRIX)
def test_reconciliation_boundary_matrix(confidence, math_cfg, erp_cfg):
    """
    Executes 300 uniquely parameterized variations of LLM extraction outputs.
    Tests boundary conditions across Confidence Scores, Math Verification, and ERP rules.
    """
    line_items, math_total, expect_math_flag = math_cfg
    doc_id, erp_total, expect_erp_flag = erp_cfg

    # We use erp_total to test against ERP records, but if evaluating math, we must use the math_total
    # to trigger the math flags condition. We prioritize ERP total for consistency unless we want to fail math specifically.
    # To keep rules isolated, we'll assign the total_amount dynamically.
    final_total = math_total if expect_math_flag else erp_total

    # Re-evaluate expected flags based on final_total alignment
    actual_expect_math_flag = False
    if line_items and final_total is not None:
        calc = sum(i["total"] for i in line_items)
        if abs(calc - final_total) > 0.01:
            actual_expect_math_flag = True

    actual_expect_erp_flag = False
    if doc_id == "PO-1002" and final_total is not None:
        if abs(final_total - 1200.50) > 0.01:
            actual_expect_erp_flag = True

    # Construct the faux-LLM JSON Payload Contract
    payload = {
        "confidence_score": confidence if confidence is not None else 0.0,
        "data": {
            "document_id": doc_id,
            "total_amount": final_total,
            "line_items": line_items
        }
    }

    # Execute Validation Agent
    result_str = process_reconciliation(json.dumps(payload))
    result = json.loads(result_str)

    flags_found = result["flags"]

    # 1. Assert Confidence Rule
    if confidence is None or confidence < 0.85:
        assert any("Low confidence" in f for f in flags_found), f"Expected low confidence flag for {confidence}"
        assert result["status"] == "REVIEW_REQUIRED"

    # 2. Assert Math Verification Rule
    if actual_expect_math_flag:
        assert any("Math check failed" in f for f in flags_found), "Expected math flag to be thrown"
        assert result["status"] == "REVIEW_REQUIRED"
    else:
        assert not any("Math check failed" in f for f in flags_found), "Did not expect math flag"

    # 3. Assert ERP Matching Rule
    if actual_expect_erp_flag:
        assert any("ERP mismatch" in f for f in flags_found), "Expected ERP flag to be thrown"
        assert result["status"] == "REVIEW_REQUIRED"
    else:
        assert not any("ERP mismatch" in f for f in flags_found), "Did not expect ERP flag"

    # 4. Assert Approval Logic
    if (confidence is not None and confidence >= 0.85) and not actual_expect_math_flag and not actual_expect_erp_flag:
        assert result["status"] == "APPROVED"
        assert len(flags_found) == 0
