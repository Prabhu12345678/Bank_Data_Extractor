# Architectural Design Document: BFSI Data Extraction Modernization

## Overview
Replaces legacy OCR extraction (Monarch) with an autonomous Document Intelligence Agent. The architecture is modular and containerized, consisting of a Backend API (FastAPI) and a Human-In-The-Loop frontend (Streamlit).

## High Level Components

1. **Upload & Ingestion**
   - Receives Multimodal Documents (PDF).
   - Backend chunks/parses basic text elements using `pdfplumber` / Tesseract vision fallbacks.

2. **Highly-Configurable LLM Strategy Factory Engine**
   - The key extraction mechanism uses LangChain and `PydanticOutputParser` to ensure schema matching.
   - LLM choice is fully controllable via ENV variables and the Factory class without rewriting orchestration paths. Choices available:
     - `claude` (Anthropic Claude 3.5 Sonnet)
     - `openai` (GPT-4)
     - `local` (Ollama/vLLM endpoints for Llama 3 / Mistral)
     - `aggregator` (Any OpenAI compatible API endpoint aggregating models)

3. **Validation & Reconciliation (Vector / Math / ERP)**
   - Flags anomalies via math checks (line items vs total validation).
   - Integrates with mock ERP/GL via identifiers to check bounds and vendor legitimacy.
   - Computes overall confidence index scores to pass/reject auto-routing.

4. **Human-In-The-Loop Frontend (HITL)**
   - Streamlit interface communicating with the Backend API.
   - Renders edge cases for manual remediation.

## Database
Configured to use **PostgreSQL with pgvector**. This provides persistent scalable state along with the capacity for RAG context storage (detecting duplicate invoices by comparing embedding similarities over prior history).

## Deployment
Packaged through an automated build script creating a <30MB GCS uploadable zip.
Running tests locally leverages a unified `docker compose up --build` environment.
