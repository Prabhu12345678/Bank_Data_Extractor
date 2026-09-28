import json
import asyncio
from src.ingestion.parser import process_ingestion
from src.extraction.extractor import DocumentExtractor

def run():
    print("1. Ingesting 'data/sample_documents/legacy_report_01.txt'...")
    with open('data/sample_documents/legacy_report_01.txt', 'rb') as f:
        file_bytes = f.read()

    ingestion_out = process_ingestion(file_bytes, "legacy_report_01.txt", "text/plain")
    ingestion_data = json.loads(ingestion_out)
    print(f"[INGESTION OUT]: Got document with {len(ingestion_data['document_text'])} characters.\n")

    print("2. Extracting structured format...")
    extractor = DocumentExtractor()
    extraction_out = extractor.extract_from_json(ingestion_out)
    print(f"[EXTRACTION OUT]:\n{extraction_out}\n")

if __name__ == "__main__":
    run()
