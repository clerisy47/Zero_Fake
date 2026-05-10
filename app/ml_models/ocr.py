from __future__ import annotations

import base64
import io
from typing import Dict, List, Optional

import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract
except ImportError:
    raise RuntimeError(
        "pytesseract is required. Install with: pip install pytesseract\n"
        "Also install Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki"
    )


class OCREngine:
    """Document OCR and text extraction using Tesseract."""
    
    def __init__(self):
        """Initialize OCR engine."""
        # Tesseract configuration
        self.config = r"--oem 3 --psm 6"
        self.languages = "eng+nep"  # English + Nepali
        
        print("✅ OCR Engine initialized (Tesseract)")
    
    @staticmethod
    def _base64_to_image(base64_str: str) -> Image.Image:
        """Convert base64 string to PIL Image."""
        try:
            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))
            return image
        except Exception as e:
            raise ValueError(f"Invalid base64 image: {e}")
    
    @staticmethod
    def _image_to_array(image: Image.Image) -> np.ndarray:
        """Convert PIL Image to numpy array."""
        image_rgb = image.convert("RGB")
        return cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2BGR)
    
    def preprocess_image_for_ocr(self, image_array: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image_array: OpenCV format image
        
        Returns:
            Preprocessed image
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Denoise
            denoised = cv2.fastNlMeansDenoising(enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21)
            
            # Thresholding
            _, binary = cv2.threshold(denoised, 127, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Dilation and erosion
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return processed
        
        except Exception as e:
            print(f"Preprocessing failed: {e}, using original image")
            return cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
    
    def extract_text(self, image_base64: str, lang: str = "eng+nep") -> Dict[str, any]:
        """
        Extract text from image using Tesseract OCR.
        
        Args:
            image_base64: Base64 encoded document image
            lang: Language codes for OCR (e.g., "eng", "nep", "eng+nep")
        
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            image = self._base64_to_image(image_base64)
            image_array = self._image_to_array(image)
            
            # Preprocess
            processed = self.preprocess_image_for_ocr(image_array)
            
            # Extract text
            text = pytesseract.image_to_string(processed, lang=lang, config=self.config)
            
            # Get detailed data
            data = pytesseract.image_to_data(processed, lang=lang, output_type=pytesseract.Output.DICT)
            
            # Calculate confidence
            confidences = [int(conf) for conf in data["conf"] if int(conf) > 0]
            avg_confidence = np.mean(confidences) / 100.0 if confidences else 0.0
            
            return {
                "extracted_text": text.strip(),
                "confidence": float(avg_confidence),
                "languages_used": lang,
                "word_count": len([w for w in text.split() if w.strip()]),
                "character_count": len(text),
                "detailed_data": {
                    "words": data["text"],
                    "confidences": confidences,
                },
            }
        
        except Exception as e:
            return {
                "extracted_text": "",
                "confidence": 0.0,
                "error": str(e),
            }
    
    def extract_structured_fields(self, image_base64: str) -> Dict[str, any]:
        """
        Extract structured fields from document.
        Looks for common patterns like names, dates, IDs, etc.
        
        Args:
            image_base64: Base64 encoded document image
        
        Returns:
            Dictionary with extracted fields
        """
        try:
            import re
            
            ocr_result = self.extract_text(image_base64)
            text = ocr_result.get("extracted_text", "")
            
            # Extract common patterns
            patterns = {
                "dates": r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}",
                "ids": r"[A-Z]{1,2}\d{6,10}",
                "emails": r"[\w\.-]+@[\w\.-]+\.\w+",
                "phone_numbers": r"(\+\d{1,3})?[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{4}",
                "names": r"[A-Z][a-z]+\s[A-Z][a-z]+",
            }
            
            extracted_fields = {
                "full_text": text,
                "confidence": ocr_result.get("confidence", 0.0),
                "fields": {},
            }
            
            for field_name, pattern in patterns.items():
                matches = re.findall(pattern, text)
                if matches:
                    extracted_fields["fields"][field_name] = matches
            
            return extracted_fields
        
        except Exception as e:
            return {
                "full_text": "",
                "confidence": 0.0,
                "error": str(e),
            }
    
    def validate_ocr_quality(self, image_base64: str, min_confidence: float = 0.6) -> Dict[str, any]:
        """
        Validate quality of OCR extraction.
        
        Args:
            image_base64: Base64 encoded document image
            min_confidence: Minimum acceptable confidence threshold
        
        Returns:
            Dictionary with quality assessment
        """
        try:
            ocr_result = self.extract_text(image_base64)
            confidence = ocr_result.get("confidence", 0.0)
            text = ocr_result.get("extracted_text", "")
            
            # Quality checks
            checks = {
                "has_text": len(text.strip()) > 10,
                "sufficient_confidence": confidence >= min_confidence,
                "word_count_valid": 5 < len(text.split()) < 500,
                "no_excessive_symbols": sum(1 for c in text if c in "!@#$%^&*()_+-=[]{}|;:,.<>?") < len(text) * 0.1,
            }
            
            # Overall quality
            quality_score = sum(checks.values()) / len(checks)
            
            if quality_score >= 0.75:
                quality_level = "high"
            elif quality_score >= 0.5:
                quality_level = "medium"
            else:
                quality_level = "low"
            
            return {
                "ocr_confidence": float(confidence),
                "quality_level": quality_level,
                "quality_score": float(quality_score),
                "checks": checks,
                "recommendation": (
                    "OCR data can be trusted" if quality_level == "high"
                    else "OCR data should be verified manually" if quality_level == "medium"
                    else "OCR quality too low, manual review required"
                ),
            }
        
        except Exception as e:
            return {
                "ocr_confidence": 0.0,
                "quality_level": "unknown",
                "error": str(e),
            }


# Global instance
_ocr_engine: Optional[OCREngine] = None


def get_ocr_engine() -> OCREngine:
    """Get or initialize OCR engine (singleton pattern)."""
    global _ocr_engine
    
    if _ocr_engine is None:
        _ocr_engine = OCREngine()
    
    return _ocr_engine
