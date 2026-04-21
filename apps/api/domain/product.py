"""Domain models for product extraction.

Defines the Pydantic schemas used throughout the extraction pipeline:
from Claude's raw JSON output through to the API response envelope.
"""

from pydantic import BaseModel, Field


class ProductVariant(BaseModel):
    """A single variant of a product (e.g. a specific size or color option)."""

    size: str | None = None
    color: str | None = None
    material: str | None = None
    sku: str | None = None
    price: float | None = None
    additional_attributes: dict[str, str] = Field(default_factory=dict)


class ExtractedProduct(BaseModel):
    """Structured product information extracted from a video transcript.

    All fields are optional or have defaults because the LLM may not be
    able to determine every attribute from the audio content.
    """

    product_name: str | None = None
    description: str | None = None
    price: float | None = None
    currency: str | None = "INR"
    category: str | None = None
    availability: str | None = None
    variants: list[ProductVariant] = Field(default_factory=list)
    additional_attributes: dict[str, str] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Result payload returned by the extraction pipeline.

    Contains only structured product data; the raw transcript is logged
    for traceability but deliberately excluded from the API response.
    """

    products: list[ExtractedProduct]


class ExtractionResponse(BaseModel):
    """Top-level API response envelope for the extract-products endpoint."""

    success: bool
    data: ExtractionResult | None = None
    error: str | None = None
