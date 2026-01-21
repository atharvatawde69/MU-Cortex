# OCR optimized for Mumbai University exam papers
import os
import sys
from pathlib import Path
from typing import Dict, List
import pdfplumber
from pdf2image import convert_from_path
from PIL import Image
import pytesseract
import logging
import cv2
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_alphabetic_ratio(text: str) -> float:
    """Calculate ratio of alphabetic characters to total characters."""
    if not text:
        return 0.0
    alpha_count = sum(1 for c in text if c.isalpha())
    total_count = len([c for c in text if not c.isspace()])
    return (alpha_count / total_count * 100) if total_count > 0 else 0.0


def deskew_image(image):
    """Detect and correct skew angle in image."""
    # Convert PIL image to numpy array
    img_array = np.array(image)
    # Convert to grayscale if needed
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Hough line transform to detect skew
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    
    if lines is not None and len(lines) > 0:
        angles = []
        for rho, theta in lines[:20]:  # Check first 20 lines
            angle = (theta * 180 / np.pi) - 90
            if -45 < angle < 45:
                angles.append(angle)
        
        if angles:
            median_angle = np.median(angles)
            if abs(median_angle) > 0.5:  # Only correct if angle > 0.5 degrees
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return Image.fromarray(rotated)
    
    return image


def preprocess_image_for_ocr(image):
    """
    Improve OCR quality for MU exam papers with advanced preprocessing.
    """
    # Convert PIL image to OpenCV format
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter for noise reduction while preserving edges
    filtered = cv2.bilateralFilter(gray, 9, 75, 75)

    # Increase contrast to remove watermark
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(filtered)

    # Apply adaptive thresholding (Gaussian)
    thresh = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )

    # Morphological closing to restore character integrity
    kernel = np.ones((2, 2), np.uint8)
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Convert back to PIL Image for pytesseract
    return Image.fromarray(closed)


def clean_ocr_text(text: str) -> str:
    """Remove noise and preserve sentence structure."""
    if not text:
        return ""
    
    lines = text.splitlines()
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # Skip single-character lines
        if len(stripped) <= 1:
            continue
        
        # Skip lines that are mostly numeric garbage (more than 70% digits)
        if stripped:
            digit_ratio = sum(1 for c in stripped if c.isdigit()) / len(stripped)
            if digit_ratio > 0.7 and len(stripped) < 10:
                continue
        
        cleaned_lines.append(line)
    
    return "\n".join(cleaned_lines)


class PDFExtractor:
    """
    Extract text from PYQ PDFs.
    Handles both text-based PDFs and scanned images.
    """
    
    def __init__(self):
        self.extracted_data = {}
    
    def extract_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF using best available method.
        
        Strategy:
        1. Try pdfplumber (for text-based PDFs)
        2. Check alphabetic ratio - if < 60%, force OCR
        3. Fall back to OCR if needed
        """
        logger.info(f"Processing: {pdf_path}")
        
        try:
            # Try pdfplumber first
            text = self._extract_text_direct(pdf_path)
            
            # Calculate overall alphabetic ratio
            if text.strip():
                alpha_ratio = calculate_alphabetic_ratio(text)
                logger.info(f"📊 Alphabetic ratio from pdfplumber: {alpha_ratio:.1f}%")
                
                # If alphabetic ratio is good (>= 60%) and text is substantial, use it
                if alpha_ratio >= 60.0 and len(text.strip()) > 100:
                    logger.info(f"✅ Using pdfplumber extraction ({len(text)} chars, {alpha_ratio:.1f}% alphabetic)")
                    return text
                else:
                    logger.warning(f"⚠️ pdfplumber text quality low ({alpha_ratio:.1f}% alphabetic) - forcing OCR")
            
            # Force OCR for better quality
            logger.info("🔄 Using image-based OCR extraction")
            text = self._extract_text_ocr(pdf_path)
            logger.info(f"✅ Extracted {len(text)} chars using OCR")
            return text
            
        except Exception as e:
            logger.error(f"❌ Extraction failed: {str(e)}")
            return ""
    
    def _extract_text_direct(self, pdf_path: str) -> str:
        text_parts = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                if page_text.strip():
                    alpha_ratio = calculate_alphabetic_ratio(page_text)
                    logger.debug(f"Page {page_num}: {alpha_ratio:.1f}% alphabetic ratio")
                    text_parts.append(f"--- Page {page_num} ---\n{page_text}")
        
        return "\n\n".join(text_parts)
    
    def _extract_text_ocr(self, pdf_path: str) -> str:
        text_parts = []
        images = convert_from_path(pdf_path, dpi=300)
        
        for page_num, image in enumerate(images, 1):
            # Deskew if needed
            deskewed = deskew_image(image)
            
            # Preprocess image
            processed = preprocess_image_for_ocr(deskewed)

            # Extract text with optimized config
            page_text = pytesseract.image_to_string(
                processed,
                lang="eng",
                config="--oem 1 --psm 4 -l eng"
            )

            # Clean the extracted text
            cleaned_text = clean_ocr_text(page_text)
            
            if cleaned_text.strip():
                alpha_ratio = calculate_alphabetic_ratio(cleaned_text)
                logger.debug(f"Page {page_num} OCR: {alpha_ratio:.1f}% alphabetic ratio")
                text_parts.append(f"--- Page {page_num} ---\n{cleaned_text}")
        
        return "\n\n".join(text_parts)
    
    def save_extracted_text(self, pdf_path: str, output_dir: str = "pyq_extracted"):
        text = self.extract_from_pdf(pdf_path)
        Path(output_dir).mkdir(exist_ok=True)
        output_path = Path(output_dir) / f"{Path(pdf_path).stem}.txt"
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        
        logger.info(f"💾 Saved extracted text to: {output_path}")
        return output_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_text.py <pdf_directory>")
        sys.exit(1)
    
    pdf_dir = sys.argv[1]
    extractor = PDFExtractor()
    pdf_files = list(Path(pdf_dir).glob("*.pdf"))
    
    logger.info(f"Found {len(pdf_files)} PDF files")
    
    for pdf_file in pdf_files:
        extractor.save_extracted_text(str(pdf_file))
    
    logger.info("✅ PDF text extraction complete")

if __name__ == "__main__":
    main()
