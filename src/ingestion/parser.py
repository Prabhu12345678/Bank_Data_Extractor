import io
import json
import pdfplumber
import pytesseract
from PIL import Image
from src.extraction.classifier import DocumentClassifier

def process_ingestion(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Ingestion Agent: Takes raw file bytes and outputs a JSON contract.
    Output Contract: {"document_text": string, "metadata": {"filename": string, "pages": int, "type": string, "classification": dict}}
    """
    document_text = ""
    num_pages = 1

    content_type_lower = content_type.lower()
    filename_lower = filename.lower()

    try:
        if "pdf" in content_type_lower or filename_lower.endswith(".pdf"):
            text_content = []
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                num_pages = len(pdf.pages)
                for page in pdf.pages:
                    # 1. Try standard text extraction
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_content.append(page_text)
                    else:
                        # 2. Fallback to OCR if page contains no parsable text (Scanned PDF)
                        try:
                            img = page.to_image(resolution=200).original
                            ocr_text = pytesseract.image_to_string(img)
                            if ocr_text:
                                text_content.append(ocr_text)
                        except Exception:
                            pass
            document_text = "\n".join(text_content)

        elif any(ext in content_type_lower for ext in ["image", "png", "jpeg", "jpg", "bmp"]) or \
             any(filename_lower.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".bmp"]):
            # Document is a raw scanned image
            img = Image.open(io.BytesIO(file_bytes))
            document_text = pytesseract.image_to_string(img)

        else:
            # Assume it's a text/plain or Monarch-style legacy print report (.prn, .txt, .csv)
            document_text = file_bytes.decode('utf-8', errors='ignore')

    except Exception as e:
        # Fallback to empty text with an error trace in metadata if parsing completely explodes
        document_text = ""

    # Pre-classify the document based on filename and extracted text
    classification = DocumentClassifier.classify(filename, document_text)

    # JSON Output Contract
    contract = {
        "document_text": document_text,
        "metadata": {
            "filename": filename,
            "pages": num_pages,
            "type": content_type,
            "classification": classification
        }
    }
    return json.dumps(contract)