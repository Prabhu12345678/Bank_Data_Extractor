import json
import asyncio
from src.ingestion.parser import process_ingestion
from src.extraction.extractor import DocumentExtractor
from src.validation.reconciliation import process_reconciliation
from unittest.mock import patch, MagicMock

@patch('src.extraction.extractor.LLMFactory.get_llm')
def run(mock_get_llm):
    # Mock LLM to avoid needing actual API keys
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    print("=== STARTING MOCK PIPELINE RUN ===\n")

    # 1. Simulate reading the legacy report test file
    print("1. Ingesting 'data/sample_documents/legacy_report_01.txt'...")
    with open('data/sample_documents/legacy_report_01.txt', 'rb') as f:
        file_bytes = f.read()

    # Call Ingestion Agent
    ingestion_out = process_ingestion(file_bytes, "legacy_report_01.txt", "text/plain")
    ingestion_data = json.loads(ingestion_out)
    print(f"[INGESTION OUT]: Got document with {len(ingestion_data['document_text'])} characters.\n")

    # 2. Simulate Extraction Agent
    print("2. Extracting structured format...")
    extractor = DocumentExtractor()

    # Mocking the actual LLM chain result for extraction
    class MockResult:
        def model_dump_json(self):
            return json.dumps({
                "confidence_score": 0.96,
                "data": {
                    "document_type": "Invoice",
                    "entity_name": "TECH FINANCES INC.",
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
        mock_chain = MagicMock()
        mock_prompt.__or__.return_value = mock_chain
        mock_chain.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = MockResult()

        extraction_out = extractor.extract_from_json(ingestion_out)
        print(f"[EXTRACTION OUT]:\n{json.dumps(json.loads(extraction_out), indent=2)}\n")

    # 3. Simulate Validation Agent
    print("3. Validating against ERP and thresholds...")
    validation_out = process_reconciliation(extraction_out)
    print(f"[VALIDATION OUT]:\n{json.dumps(json.loads(validation_out), indent=2)}\n")

if __name__ == "__main__":
    run()
