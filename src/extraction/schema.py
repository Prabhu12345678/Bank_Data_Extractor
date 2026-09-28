from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class LineItem(BaseModel):
    description: str = Field(description="Description of the item or service.")
    quantity: float = Field(description="Quantity or hours.")
    unit_price: float = Field(description="Price per unit.")
    total: float = Field(description="Total price for the line item.")
    source_excerpt: Optional[str] = Field(None, description="Exact quote from the document text justifying this line item, including the [Line N] prefix.")

    @model_validator(mode='after')
    def check_line_item_math(self) -> 'LineItem':
        # Self-correcting AI: ensure the line item total matches qty * unit_price (allow minor floating point diff)
        expected_total = self.quantity * self.unit_price
        if abs(expected_total - self.total) > 0.01:
            # If the LLM extraction is slightly off due to OCR, correct the total
            self.total = round(expected_total, 2)
        return self

class DocumentData(BaseModel):
    """Schema for Invoice or Bank Statement extraction."""
    document_type: str = Field(description="Type of document, e.g., 'Invoice', 'Bank Statement', 'Purchase Order'.")
    entity_name: Optional[str] = Field(None, description="Name of the company or bank issuing the document.")
    document_id: Optional[str] = Field(None, description="Invoice number, PO number, or statement ID.")
    date: Optional[str] = Field(None, description="Date of the document.")
    total_amount: Optional[float] = Field(None, description="Total amount due or closing balance.")
    total_tax_amount: Optional[float] = Field(0.0, description="Total tax amount applied to the invoice, if present.")
    source_excerpt: Optional[str] = Field(None, description="Exact quote from the document supporting the entity_name, document_id, date, and total_amount, including the [Line N] prefix.")
    line_items: List[LineItem] = Field(default_factory=list, description="Extracted line items or transactions in tabular format.")

class ExtractedOutput(BaseModel):
    """Final output combining data and confidence."""
    confidence_score: float = Field(..., description="Overall confidence level of extraction between 0.0 and 1.0.")
    data: DocumentData = Field(..., description="The structured extracted data.")

    @field_validator('confidence_score')
    @classmethod
    def bound_confidence_score(cls, v: float) -> float:
        """Ensure LLMs don't hallucinate confidence scores outside the 0.0 to 1.0 bounds."""
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v
