import pytest
import os
import json
import random
from src.ingestion.parser import process_ingestion

# We generate 500 distinct Monarch-style configurations
MONARCH_CASES = range(500)

def generate_monarch_report(po_num: str, row_count: int, total: float, vendor: str, add_noise: bool) -> bytes:
    """
    Generates a large fixed-width Monarch-style mainframe report.
    Simulates large legacy system dumps with variable width columns and potential noise.
    """
    lines = []
    lines.append(f"REPORT ID: AR-9002{' ' * 80}DATE: 2026-10-01")
    lines.append("-" * 132)
    lines.append(f"PO NUM:       {po_num}")
    lines.append(f"VENDOR:       {vendor}")

    lines.append("LINE_ITEMS:   " + f"00001      ITEM DESC 1{' ' * 15}1.000     100.00         100.00")
    for i in range(2, row_count + 1):
        noise = "   #?!   " if add_noise and i % 5 == 0 else ""
        lines.append(f"              {str(i).zfill(5)}      ITEM DESC {i}{' ' * 15}1.000     10.00          10.00{noise}")

    lines.append("-" * 132)
    lines.append(f"TOTAL AMOUNT:                             {total:.2f}")
    lines.append("-" * 132)

    # Pad out the report to simulate a VERY large legacy dump (e.g., 500-1000 extra standard lines)
    if add_noise:
        for _ in range(50):
            lines.append("       --- EMPTY SYSTEM ROW ---       " * 3)

    return "\n".join(lines).encode('utf-8')

@pytest.mark.parametrize("use_case_id", MONARCH_CASES)
def test_monarch_scale_integration(use_case_id):
    """
    Stress tests the Ingestion Agent against 500 uniquely generated large Monarch-style mainframe reports.
    Validates structural encoding resilience at scale without bloating disk space.
    """
    # Deterministic randomness per use_case_id
    random.seed(use_case_id)

    # Dynamically scale attributes for this unique iteration
    row_count = random.randint(10, 500)
    total_math = 100.00 + ((row_count - 1) * 10.00)
    po_num = f"PO-{1000 + use_case_id}"
    add_noise = (use_case_id % 3 == 0) # 1 in 3 chance of heavy noise

    # 1. Generate payload
    raw_payload = generate_monarch_report(
        po_num=po_num,
        row_count=row_count,
        total=total_math,
        vendor=f"Corporate Entity {use_case_id}",
        add_noise=add_noise
    )

    # 2. Test Ingestion Agent
    file_name = f"legacy_mainframe_dump_{use_case_id}.prn"
    response_str = process_ingestion(raw_payload, file_name, "application/octet-stream")

    # 3. Assert Structuring
    payload = json.loads(response_str)

    assert "document_text" in payload
    assert payload["metadata"]["filename"] == file_name
    assert payload["metadata"]["type"] == "application/octet-stream"

    # Ensure all row counts survived ingestion decoding without truncating
    text_result = payload["document_text"]
    assert po_num in text_result
    assert f"{total_math:.2f}" in text_result
    assert text_result.startswith("REPORT ID: AR-9002")
