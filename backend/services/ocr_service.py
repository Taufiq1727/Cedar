"""OCR Service - document text extraction using Tesseract."""
import os
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import pytesseract - it may not be installed
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available. OCR will use fallback mode.")

# Try to import pdf2image
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not available. PDF OCR will not work.")


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image file using Tesseract OCR."""
    if not TESSERACT_AVAILABLE:
        return _fallback_ocr(image_path)

    try:
        image = Image.open(image_path)
        # Use English + Hindi for Indian medical documents
        text = pytesseract.image_to_string(image, lang='eng')
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed for image {image_path}: {e}")
        return f"[OCR extraction failed: {str(e)}]"


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file by converting to images first."""
    if not PDF2IMAGE_AVAILABLE:
        return "[PDF processing not available. Install pdf2image and poppler.]"

    try:
        images = convert_from_path(pdf_path)
        all_text = []
        for i, image in enumerate(images):
            if TESSERACT_AVAILABLE:
                text = pytesseract.image_to_string(image, lang='eng')
                all_text.append(f"--- Page {i+1} ---\n{text}")
            else:
                all_text.append(f"--- Page {i+1} ---\n[Tesseract not available]")
        return "\n".join(all_text).strip()
    except Exception as e:
        logger.error(f"PDF OCR failed for {pdf_path}: {e}")
        return f"[PDF OCR extraction failed: {str(e)}]"


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from a document based on its file type."""
    file_type = file_type.lower()
    if file_type in ("jpg", "jpeg", "png", "bmp", "tiff"):
        return extract_text_from_image(file_path)
    elif file_type == "pdf":
        return extract_text_from_pdf(file_path)
    else:
        return f"[Unsupported file type: {file_type}]"


def _fallback_ocr(image_path: str) -> str:
    """Fallback when Tesseract is not installed - return a placeholder."""
    return (
        "[OCR engine (Tesseract) is not installed. "
        "Install Tesseract OCR to enable text extraction. "
        f"File: {os.path.basename(image_path)}]"
    )
