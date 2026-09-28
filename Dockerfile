FROM python:3.11-slim

# Install system dependencies for Tesseract, PostgreSQl, and building
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . /app

# Expose ports for FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Entrypoint will be handled via docker-compose commands for separate services
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
