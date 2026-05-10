"""ML Models Package - Advanced face recognition, document analysis, liveness detection, and OCR."""

from app.ml_models.face_recognition import get_face_recognition_engine
from app.ml_models.document_forgery import get_forgery_detection_engine
from app.ml_models.liveness_detection import get_liveness_detection_engine
from app.ml_models.ocr import get_ocr_engine

__all__ = [
    "get_face_recognition_engine",
    "get_forgery_detection_engine",
    "get_liveness_detection_engine",
    "get_ocr_engine",
]
