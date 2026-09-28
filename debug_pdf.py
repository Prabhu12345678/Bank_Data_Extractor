import io
from src.ingestion.parser import process_ingestion

with open("data/financial_data_test_files/edge_cases/password_protected_stub.pdf", "rb") as f:
    res = process_ingestion(f.read(), "password_protected_stub.pdf", "application/pdf")
    print(res)
