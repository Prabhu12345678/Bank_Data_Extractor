#!/bin/bash
set -e

# Name of the output archive
ZIP_NAME="bank_solutions_archive.zip"

echo "Building zip archive for Google Cloud Storage..."

# Remove old zip if it exists
if [ -f "$ZIP_NAME" ]; then
    rm "$ZIP_NAME"
fi

# Create the zip containing runnable code, Dockerfile, README, tests, ARCHITECTURE
zip -r "$ZIP_NAME" src/ tests/ data/ requirements.txt Dockerfile docker-compose.yml ARCHITECTURE.md README.md build_zip.sh -x "*/__pycache__/*" "*/.pytest_cache/*" "*/*.pyc" "*.env"

echo "Archive created: $ZIP_NAME"

# Check size
SIZE_BYTES=$(wc -c < "$ZIP_NAME")
MAX_BYTES=$((30 * 1024 * 1024))
if [ "$SIZE_BYTES" -gt "$MAX_BYTES" ]; then
    echo "ERROR: Archive exceeds 30MB limit ($SIZE_BYTES bytes)."
    exit 1
fi

echo "Size meets requirements ($SIZE_BYTES bytes / $MAX_BYTES bytes)."

# Generate SHA-256 for integrity verification
SHA256_HASH=$(sha256sum "$ZIP_NAME" | awk '{print $1}')
echo "SHA-256 Hash: $SHA256_HASH"

echo "Artifact ready for upload."
