"""PDF text and image extraction with vision processing."""

from typing import Dict, Any
from pypdf import PdfReader


def extract_pdf(filepath: str, process_images: bool = True) -> Dict[str, Any]:
    """
    Extract content from PDF file.

    Args:
        filepath: Path to .pdf file
        process_images: If True, process images with vision

    Returns:
        Dict with pages, images, metadata
    """
    if process_images:
        from ..services.vision import process_image

    reader = PdfReader(filepath)

    pages = []
    images = []

    for page_num, page in enumerate(reader.pages, 1):
        # Extract text
        text = page.extract_text()

        pages.append({
            "page_number": page_num,
            "content": text
        })

        # Extract images if enabled
        if process_images and hasattr(page, 'images'):
            for img_index, image in enumerate(page.images):
                try:
                    image_bytes = image.data
                    vision_result = process_image(image_bytes)

                    images.append({
                        "page_number": page_num,
                        "image_index": img_index,
                        "type": vision_result["type"],
                        "quality_score": vision_result["quality_score"],
                        "extracted_text": vision_result["extracted_text"],
                        "should_index": vision_result["should_index"]
                    })
                except Exception as e:
                    print(f"Warning: Failed to process image on page {page_num}: {e}")

    return {
        "pages": pages,
        "images": images,
        "metadata": {
            "total_pages": len(reader.pages),
            "images_processed": len(images)
        }
    }
