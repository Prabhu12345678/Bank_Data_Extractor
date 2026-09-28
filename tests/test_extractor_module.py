import json
from src.extraction.extractor import DocumentExtractor
from unittest.mock import patch, MagicMock

@patch('src.extraction.extractor.LLMFactory.get_llm')
def test_extractor_json_contract(mock_get_llm):
    # Setup mock LLM and result
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    # We will mock the invoke on the chain to avoid actual LLM calls during CI
    extractor = DocumentExtractor()

    # Mocking chain.invoke
    class MockResult:
        def model_dump_json(self):
            return json.dumps({
                "confidence_score": 0.98,
                "data": {
                    "document_type": "Invoice",
                    "entity_name": "ACME CORP",
                    "document_id": "PO-1001",
                    "date": "09/20/2026",
                    "total_amount": 450.00,
                    "line_items": [
                        {"description": "SOFTWARE LICENSING", "quantity": 1, "unit_price": 200.0, "total": 200.0},
                        {"description": "ANNUAL MAINTENANCE", "quantity": 1, "unit_price": 250.0, "total": 250.0}
                    ]
                }
            })

    with patch.object(extractor, 'prompt') as mock_prompt:
        # Mocking the chain behavior
        mock_chain = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = MockResult()

        # Test input JSON contract
        input_payload = json.dumps({
            "document_text": "MOCK TEXT FROM LEGACY REPORT",
            "metadata": {"filename": "legacy_report_01.txt"}
        })

        # Call the extractor
        output_json_str = extractor.extract_from_json(input_payload)

        # Test output JSON contract
        output_payload = json.loads(output_json_str)
        assert "confidence_score" in output_payload
        assert output_payload["confidence_score"] == 0.98

        data = output_payload["data"]
        assert data["document_id"] == "PO-1001"
        assert data["total_amount"] == 450.00
        assert len(data["line_items"]) == 2

def test_extractor_empty_contract():
    # Setup empty input handling
    extractor = DocumentExtractor()

    input_payload = json.dumps({
        "document_text": "   ",
        "metadata": {"filename": "empty.txt"}
    })

    output_json_str = extractor.extract_from_json(input_payload)
    output_payload = json.loads(output_json_str)

    assert "error" in output_payload
    assert "No document_text provided" in output_payload["error"]
