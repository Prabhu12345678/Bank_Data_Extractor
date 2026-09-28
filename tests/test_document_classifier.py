"""
Unit tests for the deterministic DocumentClassifier.
Covers all document type labels: Invoice, Tax Document, Payment,
Purchase Order, Credit Note, Remittance Advice, and Unknown.
"""
import pytest
from src.extraction.classifier import DocumentClassifier


class TestFilenameClassification:
    """Validates that filename patterns alone produce the correct dominant label."""

    def test_invoice_filename(self):
        result = DocumentClassifier.classify("invoice_001.pdf", "")
        assert result["dominant_label"] == "Invoice"
        assert result["confidence"] >= 0.4

    def test_inv_abbreviation_filename(self):
        result = DocumentClassifier.classify("inv_2026_09.pdf", "")
        assert result["dominant_label"] == "Invoice"

    def test_payment_filename(self):
        result = DocumentClassifier.classify("payment_gbp.pdf", "")
        assert result["dominant_label"] == "Payment"

    def test_pmt_abbreviation_filename(self):
        result = DocumentClassifier.classify("pmt_batch.csv", "")
        assert result["dominant_label"] == "Payment"

    def test_purchase_order_filename(self):
        result = DocumentClassifier.classify("purchase_order_multi.pdf", "")
        assert result["dominant_label"] == "Purchase Order"

    def test_po_abbreviation_filename(self):
        result = DocumentClassifier.classify("po_1002.pdf", "")
        assert result["dominant_label"] == "Purchase Order"

    def test_credit_filename(self):
        result = DocumentClassifier.classify("credit_note_abc.pdf", "")
        assert result["dominant_label"] == "Credit Note"

    def test_remittance_filename(self):
        result = DocumentClassifier.classify("remittance_advice_q3.pdf", "")
        assert result["dominant_label"] == "Remittance Advice"

    def test_tax_filename(self):
        result = DocumentClassifier.classify("tax_invoice_2026.pdf", "")
        assert result["dominant_label"] in ("Invoice", "Tax Document")

    def test_unknown_filename_no_text(self):
        result = DocumentClassifier.classify("report_xyz.prn", "")
        assert result["dominant_label"] == "Unknown"
        assert result["confidence"] == 0.4


class TestTextLayerClassification:
    """Validates keyword-based text detection overrides or supplements filename hints."""

    def test_invoice_text_keyword(self):
        text = "INVOICE\nBilled To: Acme Corp\nTotal: $500.00"
        result = DocumentClassifier.classify("document.pdf", text)
        assert result["dominant_label"] == "Invoice"
        assert result["confidence"] >= 0.65

    def test_billing_text_keyword(self):
        text = "BILLING STATEMENT\nPeriod: September 2026"
        result = DocumentClassifier.classify("doc.txt", text)
        assert result["dominant_label"] == "Invoice"

    def test_tax_invoice_keyword(self):
        text = "TAX INVOICE\nGST Invoice No: TI-0042\nVAT: 18%"
        result = DocumentClassifier.classify("document.pdf", text)
        assert result["dominant_label"] == "Tax Document"

    def test_gst_invoice_keyword(self):
        text = "GST INVOICE\nSeller: XYZ Pvt Ltd\nTotal Taxable: $300.00"
        result = DocumentClassifier.classify("doc.pdf", text)
        assert result["dominant_label"] == "Tax Document"

    def test_payment_ach_keyword(self):
        text = "ACH CREDIT RECEIVED\nAmount: $1200.50\nDate: 2026-09-10"
        result = DocumentClassifier.classify("doc.txt", text)
        assert result["dominant_label"] == "Payment"

    def test_remittance_advice_keyword(self):
        text = "REMITTANCE ADVICE\nRef: REF-001\nInvoice Settled: INV-9991"
        result = DocumentClassifier.classify("doc.txt", text)
        assert result["dominant_label"] == "Remittance Advice"

    def test_remittance_slip_keyword(self):
        text = "REMITTANCE SLIP\nPayer: Vendor Corp"
        result = DocumentClassifier.classify("doc.pdf", text)
        assert result["dominant_label"] == "Remittance Advice"

    def test_credit_note_keyword(self):
        text = "CREDIT NOTE\nOriginal Invoice: INV-1000\nCredit Amount: $50.00"
        result = DocumentClassifier.classify("doc.pdf", text)
        assert result["dominant_label"] == "Credit Note"

    def test_credit_memo_keyword(self):
        text = "CREDIT MEMO\nCM-2026-001\nReason: Return"
        result = DocumentClassifier.classify("doc.pdf", text)
        assert result["dominant_label"] == "Credit Note"

    def test_purchase_order_keyword(self):
        text = "PURCHASE ORDER\nPO # 1002\nApproved For: $1200.50"
        result = DocumentClassifier.classify("doc.pdf", text)
        assert result["dominant_label"] == "Purchase Order"

    def test_work_order_keyword(self):
        text = "WORK ORDER\nWO-5021\nDepartment: Engineering"
        result = DocumentClassifier.classify("doc.pdf", text)
        assert result["dominant_label"] == "Purchase Order"

    def test_receipt_keyword(self):
        text = "RECEIPT\nPaid: $75.00\nThank you for your payment."
        result = DocumentClassifier.classify("doc.pdf", text)
        assert result["dominant_label"] == "Payment"

    def test_text_overrides_filename(self):
        # Filename says 'payment' but text clearly says purchase order
        text = "PURCHASE ORDER\nP.O. # 9901\nApproved amount: $500"
        result = DocumentClassifier.classify("payment_ref.pdf", text)
        # Text keyword (0.65) + filename (0.4 from 'pay') — PO text is dominant
        assert result["dominant_label"] == "Purchase Order"


class TestConfidenceScoring:
    """Validates confidence score bounds and cumulative scoring behavior."""

    def test_filename_only_confidence(self):
        result = DocumentClassifier.classify("invoice_simple.pdf", "")
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["confidence"] == 0.4

    def test_combined_filename_and_text_confidence(self):
        # Both filename and text say invoice — confidence should be capped at 1.0
        text = "TAX INVOICE\nTotal: $1000"
        result = DocumentClassifier.classify("invoice_tax_2026.pdf", text)
        assert result["confidence"] <= 1.0

    def test_confidence_never_exceeds_one(self):
        # Multiple matching signals should cap at 1.0
        text = "INVOICE BILLING TAX INVOICE VAT INVOICE GST INVOICE account receivable"
        result = DocumentClassifier.classify("invoice_credit_tax.pdf", text)
        for conf in result["all_labels"].values():
            assert conf <= 1.0

    def test_all_labels_returned(self):
        text = "INVOICE TAX INVOICE PAYMENT REMITTANCE ADVICE"
        result = DocumentClassifier.classify("doc.pdf", text)
        assert "all_labels" in result
        assert len(result["all_labels"]) >= 1

    def test_unknown_default_confidence(self):
        result = DocumentClassifier.classify("random_file.bin", "")
        assert result["dominant_label"] == "Unknown"
        assert result["confidence"] == 0.4


class TestEdgeCases:
    """Validates classifier robustness against malformed or ambiguous inputs."""

    def test_empty_filename_and_text(self):
        result = DocumentClassifier.classify("", "")
        assert result["dominant_label"] == "Unknown"

    def test_very_long_text_truncated(self):
        # Classifier should only inspect first 3000 chars — extra content irrelevant
        filler = "X " * 5000
        text = filler + "INVOICE\n"  # keyword is AFTER the 3000 char boundary
        result = DocumentClassifier.classify("doc.pdf", text)
        # The keyword "INVOICE" is beyond the 3000 char window — filename drives classification
        assert result["dominant_label"] == "Unknown"

    def test_text_within_window_classified(self):
        keyword_text = "INVOICE\nBilled To: Corp" + ("X " * 2000)  # keyword within first 3000
        result = DocumentClassifier.classify("file.pdf", keyword_text)
        assert result["dominant_label"] == "Invoice"

    def test_garbled_bytes_decoded(self):
        # Simulates what the parser does with errors='ignore' for legacy .prn files
        raw = b"INVOICE\x00\x01\x02 Total: $500"
        text = raw.decode("utf-8", errors="ignore")
        result = DocumentClassifier.classify("legacy.prn", text)
        assert result["dominant_label"] == "Invoice"

    def test_mixed_case_keywords(self):
        # Regex is case-insensitive
        result = DocumentClassifier.classify("doc.pdf", "InVoiCe\nBilled to: ABC")
        assert result["dominant_label"] == "Invoice"

    def test_special_characters_in_filename(self):
        result = DocumentClassifier.classify("INV_2026-09-26 (FINAL).PDF", "")
        assert result["dominant_label"] == "Invoice"

    def test_csv_payment_feed(self):
        # orders_export.csv / payments_batch.csv type
        text = "date,amount,reference,type\n2026-09-01,500.00,REF001,payment\n"
        result = DocumentClassifier.classify("payments_batch.csv", text)
        assert result["dominant_label"] == "Payment"

    def test_monarch_prn_unknown(self):
        text = "REPORT ID: AR-9002          DATE: 2026-10-01\n" + "-" * 80
        result = DocumentClassifier.classify("legacy_mainframe_dump_0.prn", text)
        # No keyword match → Unknown; that's correct behavior for raw Monarch dumps
        assert result["dominant_label"] == "Unknown"
