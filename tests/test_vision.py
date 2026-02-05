"""Tests for Gemini vision processing."""

import pytest
from unittest.mock import Mock, patch


def test_classify_image_returns_type():
    """Should classify image as chart|table|diagram|photo."""
    from app.services.vision import classify_image

    mock_response = Mock()
    mock_response.text = "chart"

    with patch("app.services.vision.client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response

        result = classify_image(b"fake_image_bytes")

        assert result in ["chart", "table", "diagram", "text_screenshot", "photo", "decorative"]
        assert result == "chart"


def test_extract_image_content_returns_text():
    """Should extract text from image."""
    from app.services.vision import extract_image_content

    mock_response = Mock()
    mock_response.text = "Sales Q1 2026: $1.2M revenue, 15% growth"

    with patch("app.services.vision.client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response

        result = extract_image_content(b"fake_chart_bytes", "chart")

        assert "Sales" in result
        assert "1.2M" in result


def test_get_quality_score_for_type():
    """Should return correct quality score for image type."""
    from app.services.vision import get_quality_score_for_type

    assert get_quality_score_for_type("chart") == 1.0
    assert get_quality_score_for_type("table") == 1.0
    assert get_quality_score_for_type("diagram") == 0.9
    assert get_quality_score_for_type("photo") == 0.3
    assert get_quality_score_for_type("decorative") == 0.1


def test_process_image_full_pipeline():
    """Should classify, extract, and return complete result."""
    from app.services.vision import process_image

    mock_classify = Mock()
    mock_classify.text = "chart"

    mock_extract = Mock()
    mock_extract.text = "Revenue data Q1 2026"

    with patch("app.services.vision.client") as mock_client:
        mock_client.models.generate_content.side_effect = [mock_classify, mock_extract]

        result = process_image(b"fake_bytes")

        assert result["type"] == "chart"
        assert result["quality_score"] == 1.0
        assert result["extracted_text"] == "Revenue data Q1 2026"
        assert result["should_index"] is True


def test_process_image_skips_low_quality():
    """Should skip extraction for low-quality images."""
    from app.services.vision import process_image

    mock_response = Mock()
    mock_response.text = "decorative"

    with patch("app.services.vision.client") as mock_client:
        mock_client.models.generate_content.return_value = mock_response

        result = process_image(b"fake_bytes")

        assert result["type"] == "decorative"
        assert result["quality_score"] == 0.1
        assert result["extracted_text"] == ""
        assert result["should_index"] is False
