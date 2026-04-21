"""Claude-based product extraction client.

Sends a video transcript to the Anthropic Claude API and parses the
structured JSON response into validated ExtractedProduct models.
"""

import json
import logging

from anthropic import APIError, Anthropic
from pydantic import ValidationError

from apps.api.core.exceptions import ProductExtractionError
from apps.api.domain.product import ExtractedProduct

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a product data extraction specialist for an e-commerce platform.
You will be given a transcript from a video (typically an Instagram Reel) that describes
one or more products. Extract every product mentioned into structured JSON.

Rules:
- Extract ALL products mentioned, even if details are sparse.
- If a field is not mentioned, omit it or set it to null.
- Prices: extract numeric values. If a currency is mentioned, use its ISO 4217 code.
  If no currency is mentioned, default to "INR".
- Variants: if the speaker mentions multiple sizes, colors, or materials for the same
  product, list them as separate variant objects.
- additional_attributes: capture any product attribute that does not fit the standard
  fields (e.g., "weight", "warranty", "origin").
- Return ONLY a JSON array of product objects. No markdown, no explanation."""

USER_PROMPT_TEMPLATE = """\
Extract structured product information from this video transcript:

---
{transcript}
---

Return a JSON array where each element has this shape:
{{
  "product_name": "string or null",
  "description": "string or null",
  "price": number or null,
  "currency": "string (ISO 4217) or null",
  "category": "string or null",
  "availability": "string or null",
  "variants": [
    {{
      "size": "string or null",
      "color": "string or null",
      "material": "string or null",
      "sku": "string or null",
      "price": number or null,
      "additional_attributes": {{}}
    }}
  ],
  "additional_attributes": {{}}
}}"""


def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences that LLMs sometimes wrap around JSON."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("\n", 1)[0]
    return cleaned.strip()


def extract_products(
    transcript: str,
    api_key: str,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
) -> list[ExtractedProduct]:
    """Call Claude to extract structured product data from a transcript.

    Raises ProductExtractionError on API failures, unparseable responses,
    or validation errors against the ExtractedProduct schema.
    """
    client = Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(transcript=transcript),
                },
            ],
        )
    except APIError as exc:
        raise ProductExtractionError(
            f"Claude API request failed: {exc}"
        ) from exc

    raw_text = message.content[0].text
    logger.debug("Claude raw response: %s", raw_text)
    cleaned = _strip_code_fences(raw_text)

    try:
        products_raw = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ProductExtractionError(
            f"Claude returned invalid JSON: {exc}"
        ) from exc

    if not isinstance(products_raw, list):
        raise ProductExtractionError(
            f"Expected a JSON array from Claude, got {type(products_raw).__name__}"
        )

    try:
        return [ExtractedProduct.model_validate(p) for p in products_raw]
    except ValidationError as exc:
        raise ProductExtractionError(
            f"Product data validation failed: {exc}"
        ) from exc
