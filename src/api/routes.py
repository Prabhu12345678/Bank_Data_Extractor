from fastapi import APIRouter, UploadFile, File, HTTPException
from src.ingestion.parser import process_ingestion
from src.extraction.extractor import DocumentExtractor
from src.validation.reconciliation import process_reconciliation
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize extractor component
try:
    extractor = DocumentExtractor()
except Exception as e:
    logger.error(f"Failed to initialize LLM extractor: {e}")
    extractor = None

@router.post("/process-document")
async def process_document(file: UploadFile = File(...)):
    """
    Orchestrates the pipeline by chaining JSON contracts between agents.
    """
    valid_extensions = (".pdf", ".txt", ".prn", ".log", ".csv", ".png", ".jpg", ".jpeg", ".bmp", ".tiff")
    if not hasattr(file, 'filename') or not file.filename.lower().endswith(valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {valid_extensions}"
        )

    if extractor is None:
        raise HTTPException(status_code=500, detail="Extraction engine not initialized (check LLM config).")

    try:
        # Step 1: Ingestion Agent
        file_bytes = await file.read()
        content_type = file.content_type or "text/plain"

        # We pass content_type to parse either PDFs or Monarch-style legacy text dumps
        ingestion_json_out = process_ingestion(file_bytes, file.filename, content_type)

        # Step 2: Extraction Agent (takes JSON contract -> returns JSON contract)
        extraction_json_out = extractor.extract_from_json(ingestion_json_out)

        # Step 3: Validation Agent (takes JSON contract -> returns JSON contract)
        validation_json_out = process_reconciliation(extraction_json_out)

        # Convert final JSON string response back to a dict for FastAPI to serialize to client
        return json.loads(validation_json_out)

    except Exception as e:
        logger.error(f"Error processing workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
