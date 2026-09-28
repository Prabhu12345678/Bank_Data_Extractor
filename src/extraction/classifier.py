"""
Deterministic document classifier.
Uses filename patterns, structural text cues, and header keywords.
"""
import re

INVOICE_KEYWORDS = re.compile(r"\b(invoice|bill|billing|tax invoice|account receivable)\b", re.IGNORECASE)
TAX_KEYWORDS = re.compile(r"\b(tax invoice|vat invoice|gst invoice|tax document|tax receipt)\b", re.IGNORECASE)
PAYMENT_KEYWORDS = re.compile(r"\b(payment|remittance|receipt|paid|ach credit|bank transfer)\b", re.IGNORECASE)
ORDER_KEYWORDS = re.compile(r"\b(purchase order|p\.?o\.?\s*#|order confirmation|work order)\b", re.IGNORECASE)
CREDIT_KEYWORDS = re.compile(r"\b(credit note|credit memo|credit invoice)\b", re.IGNORECASE)
REMITTANCE_KEYWORDS = re.compile(r"\b(remittance advice|remittance slip)\b", re.IGNORECASE)

FILENAME_PATTERNS = {
    re.compile(r"(invoice|inv)", re.IGNORECASE): "Invoice",
    re.compile(r"(payment|pay|pmt)", re.IGNORECASE): "Payment",
    re.compile(r"(order|(?:^|[^a-zA-Z])po(?:[^a-zA-Z]|$)|purchase)", re.IGNORECASE): "Purchase Order",
    re.compile(r"(credit)", re.IGNORECASE): "Credit Note",
    re.compile(r"(remittance)", re.IGNORECASE): "Remittance Advice",
    re.compile(r"(tax)", re.IGNORECASE): "Tax Document",
}

class DocumentClassifier:
    """
    Returns deterministic classification labels and confidences.
    """
    @staticmethod
    def classify(filename: str, text_excerpt: str) -> dict:
        labels_conf = {}

        # --- Filename hints (lower weight) ---
        for pattern, label in FILENAME_PATTERNS.items():
            if pattern.search(filename):
                current = labels_conf.get(label, 0.0)
                labels_conf[label] = min(current + 0.4, 1.0)

        # --- Text-layer keyword detection (higher weight) ---
        snippet = text_excerpt[:3000]

        if INVOICE_KEYWORDS.search(snippet):
            labels_conf["Invoice"] = min(labels_conf.get("Invoice", 0.0) + 0.65, 1.0)

        if TAX_KEYWORDS.search(snippet):
            labels_conf["Tax Document"] = min(labels_conf.get("Tax Document", 0.0) + 0.85, 1.0)
            # Do not increment Invoice massively if it's explicitly a Tax document
            labels_conf["Invoice"] = min(labels_conf.get("Invoice", 0.0) + 0.1, 1.0)

        if PAYMENT_KEYWORDS.search(snippet):
            labels_conf["Payment"] = min(labels_conf.get("Payment", 0.0) + 0.65, 1.0)

        if ORDER_KEYWORDS.search(snippet):
            labels_conf["Purchase Order"] = min(labels_conf.get("Purchase Order", 0.0) + 0.65, 1.0)

        if CREDIT_KEYWORDS.search(snippet):
            labels_conf["Credit Note"] = min(labels_conf.get("Credit Note", 0.0) + 0.75, 1.0)

        if REMITTANCE_KEYWORDS.search(snippet):
            labels_conf["Remittance Advice"] = min(labels_conf.get("Remittance Advice", 0.0) + 0.75, 1.0)

        if not labels_conf:
            labels_conf["Unknown"] = 0.4

        # Select the dominant label
        dominant_label = max(labels_conf, key=labels_conf.get)
        confidence = labels_conf[dominant_label]

        return {
            "dominant_label": dominant_label,
            "confidence": confidence,
            "all_labels": labels_conf
        }
