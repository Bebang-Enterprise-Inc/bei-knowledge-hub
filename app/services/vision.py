"""Gemini 2.0 Flash vision processing for Knowledge Hub.

Classifies images (chart/table/diagram/photo), extracts content,
auto-scores by type for quality filtering.
"""

import base64
from typing import Dict, Any
from google import genai

from ..config import config

# Initialize Gemini client
client = genai.Client(api_key=config.gemini_api_key)

# Quality scoring by image type
QUALITY_SCORES = {
    "chart": 1.0,
    "table": 1.0,
    "diagram": 0.9,
    "text_screenshot": 0.9,
    "photo": 0.3,  # Evidence photos - low priority
    "decorative": 0.1  # Logos, backgrounds
}

QUALITY_THRESHOLD = 0.5  # Only extract content if >= this score


def classify_image(image_bytes: bytes) -> str:
    """
    Classify image type using Gemini vision.

    Args:
        image_bytes: Raw image bytes (JPEG, PNG, etc.)

    Returns:
        Type string: chart|table|diagram|text_screenshot|photo|decorative
    """
    # Encode image to base64
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    prompt = """Classify this image into ONE of these categories:
- chart: Bar chart, line graph, pie chart, any data visualization
- table: Spreadsheet, data table, comparison matrix
- diagram: Flowchart, org chart, process diagram, architecture diagram
- text_screenshot: Screenshot with text content (emails, documents, slides)
- photo: Photograph of people, products, stores, events
- decorative: Logo, background image, decorative graphic

Return ONLY the category name, no explanation."""

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_b64
                        }
                    }
                ]
            }
        ]
    )

    classification = response.text.strip().lower()

    # Validate classification
    valid_types = ["chart", "table", "diagram", "text_screenshot", "photo", "decorative"]
    if classification not in valid_types:
        # Default to photo if unclear
        classification = "photo"

    return classification


def extract_image_content(image_bytes: bytes, image_type: str) -> str:
    """
    Extract text and data from image using Gemini vision.

    Args:
        image_bytes: Raw image bytes
        image_type: Image classification (for prompt optimization)

    Returns:
        Extracted text content
    """
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')

    # Type-specific extraction prompts
    prompts = {
        "chart": "Extract all data, labels, values, and insights from this chart. Include axis labels, legend, data points, and any annotations.",
        "table": "Extract all data from this table. Include column headers, row labels, and all cell values. Preserve structure.",
        "diagram": "Describe this diagram in detail. Include all text labels, connections, flow, and relationships between elements.",
        "text_screenshot": "Extract all visible text from this screenshot. Preserve formatting and structure.",
        "photo": "Describe what's visible in this photo. Include any text, signage, or relevant details."
    }

    prompt = prompts.get(image_type, "Extract all text and relevant information from this image.")

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_b64
                        }
                    }
                ]
            }
        ]
    )

    return response.text.strip()


def get_quality_score_for_type(image_type: str) -> float:
    """
    Get quality score for image type.

    Args:
        image_type: Image classification

    Returns:
        Quality score (0.0-1.0)
    """
    return QUALITY_SCORES.get(image_type, 0.5)


def process_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Full pipeline: classify, extract, score.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Dict with type, quality_score, extracted_text, should_index
    """
    # Step 1: Classify
    image_type = classify_image(image_bytes)

    # Step 2: Get quality score
    quality_score = get_quality_score_for_type(image_type)

    # Step 3: Extract content if high quality
    extracted_text = ""
    should_index = quality_score >= QUALITY_THRESHOLD

    if should_index:
        extracted_text = extract_image_content(image_bytes, image_type)

    return {
        "type": image_type,
        "quality_score": quality_score,
        "extracted_text": extracted_text,
        "should_index": should_index
    }
