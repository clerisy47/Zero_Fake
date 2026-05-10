from __future__ import annotations

import base64
import io
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

try:
    import tensorflow as tf
    from tensorflow.keras.applications import ResNet50, VGG16
    from tensorflow.keras.preprocessing import image as keras_image
except ImportError:
    raise RuntimeError("TensorFlow is required. Install with: pip install tensorflow")


class DocumentForgeryDetectionEngine:
    """CNN-based document forgery detection."""
    
    def __init__(self):
        """Initialize forgery detection models."""
        self.device = "cpu"  # Use CPU by default, GPU optional
        
        # Pre-trained CNN models
        self.resnet_model = ResNet50(weights="imagenet", include_top=False, pooling="avg")
        self.vgg_model = VGG16(weights="imagenet", include_top=False, pooling="avg")
        
        print("✅ Document Forgery Detection Engine initialized")
    
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
        return np.array(image_rgb)
    
    def error_level_analysis(self, image_base64: str) -> Dict[str, float]:
        """
        Error Level Analysis (ELA) for forgery detection.
        Detects compression inconsistencies that indicate splicing/editing.
        
        Args:
            image_base64: Base64 encoded document image
        
        Returns:
            Dictionary with ELA scores
        """
        try:
            image = self._base64_to_image(image_base64)
            image_array = self._image_to_array(image)
            
            # Convert to BGR for OpenCV
            if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image_array
            
            # Save and re-load with JPEG compression to find differences
            _, buffer = cv2.imencode(".jpg", image_bgr, [cv2.IMWRITE_JPEG_QUALITY, 90])
            recompressed = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
            
            # Calculate difference
            difference = cv2.absdiff(image_bgr, recompressed)
            
            # Extract anomaly regions
            b, g, r = cv2.split(difference)
            
            # Calculate statistics
            ela_score = {
                "blue_anomaly": float(np.mean(b) / 255.0),
                "green_anomaly": float(np.mean(g) / 255.0),
                "red_anomaly": float(np.mean(r) / 255.0),
                "total_anomaly": float(np.mean(difference) / 255.0),
                "max_anomaly": float(np.max(difference) / 255.0),
            }
            
            # Normalization
            ela_score["ela_risk"] = min(1.0, ela_score["total_anomaly"] * 5.0)
            
            return ela_score
        
        except Exception as e:
            raise ValueError(f"ELA analysis failed: {e}")
    
    def cnn_forgery_detection(self, image_base64: str, model_name: str = "resnet") -> Tuple[float, Dict]:
        """
        CNN-based forgery detection using pre-trained models.
        
        Args:
            image_base64: Base64 encoded document image
            model_name: "resnet" or "vgg"
        
        Returns:
            Tuple of (forgery_score, details_dict)
        """
        try:
            image = self._base64_to_image(image_base64)
            image_resized = image.resize((224, 224))
            image_array = np.array(image_resized)
            
            # Preprocess for CNN
            image_expanded = np.expand_dims(image_array, axis=0)
            from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
            from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_preprocess
            
            if model_name == "resnet":
                image_preprocessed = resnet_preprocess(image_expanded.copy())
                features = self.resnet_model.predict(image_preprocessed, verbose=0)
            else:
                image_preprocessed = vgg_preprocess(image_expanded.copy())
                features = self.vgg_model.predict(image_preprocessed, verbose=0)
            
            # Analyze feature distribution for anomalies
            feature_mean = np.mean(features)
            feature_std = np.std(features)
            feature_anomaly = np.abs(features - feature_mean) / (feature_std + 1e-5)
            
            # Compute forgery score
            forgery_score = float(min(1.0, np.mean(feature_anomaly) / 10.0))
            
            return forgery_score, {
                "model": model_name,
                "feature_mean": float(feature_mean),
                "feature_std": float(feature_std),
                "anomaly_regions": int(np.sum(feature_anomaly > 2.0)),
            }
        
        except Exception as e:
            raise ValueError(f"CNN forgery detection failed: {e}")
    
    def detect_document_manipulations(self, image_base64: str) -> Dict[str, any]:
        """
        Comprehensive document manipulation detection.
        
        Args:
            image_base64: Base64 encoded document image
        
        Returns:
            Dictionary with multiple forgery detection results
        """
        try:
            # Run multiple detection methods
            ela_results = self.error_level_analysis(image_base64)
            cnn_resnet_score, cnn_resnet_details = self.cnn_forgery_detection(image_base64, "resnet")
            cnn_vgg_score, cnn_vgg_details = self.cnn_forgery_detection(image_base64, "vgg")
            
            # Ensemble score
            ensemble_score = (ela_results["ela_risk"] + cnn_resnet_score + cnn_vgg_score) / 3.0
            
            # Risk classification
            if ensemble_score < 0.3:
                risk_level = "low"
            elif ensemble_score < 0.6:
                risk_level = "medium"
            elif ensemble_score < 0.8:
                risk_level = "high"
            else:
                risk_level = "critical"
            
            return {
                "ensemble_forgery_score": float(ensemble_score),
                "risk_level": risk_level,
                "ela_analysis": ela_results,
                "cnn_resnet": {
                    "forgery_score": float(cnn_resnet_score),
                    "details": cnn_resnet_details,
                },
                "cnn_vgg": {
                    "forgery_score": float(cnn_vgg_score),
                    "details": cnn_vgg_details,
                },
                "recommendation": (
                    "Document appears genuine" if risk_level == "low"
                    else "Document has suspicious features" if risk_level == "medium"
                    else "Document shows strong signs of manipulation" if risk_level == "high"
                    else "Document appears to be heavily forged"
                ),
            }
        
        except Exception as e:
            return {
                "ensemble_forgery_score": 0.0,
                "risk_level": "unknown",
                "error": str(e),
            }


# Global instance
_forgery_detection_engine: Optional[DocumentForgeryDetectionEngine] = None


def get_forgery_detection_engine() -> DocumentForgeryDetectionEngine:
    """Get or initialize forgery detection engine (singleton pattern)."""
    global _forgery_detection_engine
    
    if _forgery_detection_engine is None:
        _forgery_detection_engine = DocumentForgeryDetectionEngine()
    
    return _forgery_detection_engine
