# Finance Data Extraction Modernization

Banking, Financial Services & Insurance (BFSI) Document Intelligence Agent.

This project modernizes enterprise financial document processing by transitioning from rigid, legacy Monarch-based templates and rigid OCR rules to an autonomous **Document Intelligence Agent**. The system dynamically ingests, parses, validates, and extracts complex tables and key-value pairs from unstructured and semi-structured documents (invoices, receipts, bank statements, ledger extracts, legacy `.prn` dumps).

## Core Capabilities
- **Multimodal Document Ingestion**: Supports digital PDFs, raw scanned images (`.png`, `.jpg`, `.bmp`, `.tiff`) via OCR fallback, and legacy flat files (`.txt`, `.prn`, `.csv`).
- **Dynamic AI Extraction**: Employs LangChain Pydantic parsers to extract normalized data without fixed positional templates.
- **Configurable LLM Strategy**: Agnostic factory pattern supporting Claude 3.5 Sonnet, GPT-4o, localized open-source deployments (Ollama/vLLM), and aggregate proxies.
- **Two-Way / Three-Way Matching**: Automated reconciliation linking item-level math to header totals, and validating documents against enterprise ERP systems.
- **Anomaly Detection**: Flags mathematical discrepancies, duplicate invoices, ERP mismatches, and enforces minimum AI confidence scores for straight-through-processing.
- **Human-in-the-Loop (HITL)**: Streamlit-based interactive UI to safely review flagged edge cases.

---

## 🛠️ System Requirements & Dependencies

To run this project "anywhere on any platform" (Linux/macOS/Windows), you can use **Docker (Recommended)** for a fully containerized environment, or deploy natively via **Python**.

### Option A: Docker (Cross-Platform / Production)
- **Docker** and **Docker Compose** installed.

### Option B: Native Python (Locally on Linux / macOS / Windows)
If deploying without Docker, ensure you have the following system libraries installed for the OCR/PDF fallback engines:
- **Python 3.11+**
- **Tesseract OCR**: 
  - Ubuntu/Debian: `sudo apt-get install tesseract-ocr tesseract-ocr-eng`
  - macOS: `brew install tesseract`
  - Windows: Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

---

## ⚙️ Configuration (.env)

The system relies heavily on environment variables for configurability. Create a `.env` file at the root of the project (copy `.env.example` if available).

```env
# Document Database Connections
DB_HOST=localhost   # 'db' if using docker-compose
DB_PORT=5432
DB_USER=extractor
DB_PASSWORD=extractorpass
DB_NAME=extractor_db

# Core LLM Orchestration
# Supported Options: mock, claude, openai, ollama, aggregator
LLM_PROVIDER=aggregator

# Required if using Aggregator APIs
AGGREGATOR_URL=http://localhost:20128/v1
AGGREGATOR_API_KEY=sk-your-aggregator-key
AGGREGATOR_MODEL=auto/best-fast

# Required if using direct commercial LLMs
ANTHROPIC_API_KEY=sk-ant-your-claude-key
OPENAI_API_KEY=sk-your-openai-key

# Rules & Thresholds
CONFIDENCE_THRESHOLD=0.85
```

---

## 🚀 How to Build and Run

### Running via Docker (Recommended)
This spins up the FastAPI Backend, Streamlit Frontend, and a PostgreSQL/pgvector database.

```bash
# 1. Build and boot the stack
docker compose up --build -d

# 2. Monitor processing logs
docker compose logs -f api
```

### Running Natively via Python (Development)
```bash
# 1. Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the Backend API (FastAPI)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start the Frontend (Streamlit) in another terminal
streamlit run src/frontend/app.py
```

---

## 💻 Accessing the Application

- **REST API (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Interactive Review UI (HITL):** [http://localhost:8501](http://localhost:8501)

### Quick Test via CLI
You can test the system locally by submitting an arbitrary payload directly from the included corpus:
```bash
curl -X POST http://localhost:8000/api/v1/process-document \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data/financial_data_test_files/scanned/invoice_photo_good.png"
```

---

## 🧪 Quality Assurance & Testing Suite

The system includes an exhaustive **800+ test suite** emphasizing validation boundary conditions and large monolithic stress-testing paradigms.

```bash
# Make sure your venv is activated
PYTHONPATH=. pytest tests/ -v
```
**Test Coverage Includes:**
- **Corpus Evaluation** (`test_corpus_integration.py`): Ingests the `data/financial_data_test_files` testing real-world PDFs, corrupted dumps, and scanned image extractions.
- **Combinatorial Boundaries** (`test_validation_comprehensive.py`): 300 parametric checks against logic matrixes for exact vs. fuzzy numeric ERP alignment rules.
- **Mainframe Scale** (`test_monarch_scale_integration.py`): Mass generation of 500 multi-thousand-row Monarch-style `.prn` files guaranteeing structural decoding boundaries.
- **Chaos / Edge Cases** (`test_edge_cases_integration.py`): Intentional assertions against zero-volume transactions, negative sums, massive decimal cascades, and completely untyped binary injections.

---

## 📦 Packaging for Cloud Distribution (Google Cloud Storage)

For finalized continuous delivery and GCS uploads fulfilling the strict delivery specs (<30MB limit):
```bash
chmod +x build_zip.sh
./build_zip.sh
```
This utility bundles the `src/`, `tests/`, `data/`, architectural documents, and manifests, applies a clean `.gitignore` filter (`__pycache__`, etc.), checks the size constraints, and produces a SHA-256 verifiable artifact: `bank_solutions_archive.zip`.# Bank_Data_Extractor
