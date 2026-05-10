from __future__ import annotations

import base64
import io
from typing import Dict, Optional, Tuple

import cv2
import numpy as np
from PIL import Image

try:
    import mediapipe as mp
except ImportError:
    raise RuntimeError("MediaPipe is required. Install with: pip install mediapipe")


class LivenessDetectionEngine:
    """Liveness detection using OpenCV and MediaPipe."""
    
    def __init__(self):
        """Initialize liveness detection models."""
        # MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_face_mesh = mp.solutions.face_mesh
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Initialize detectors
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=1,  # 1 for full-range (back camera), 0 for short-range (front camera)
            min_detection_confidence=0.5,
        )
        
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        
        print("✅ Liveness Detection Engine initialized")
    
    @staticmethod
    def _base64_to_array(base64_str: str) -> np.ndarray:
        """Convert base64 string to numpy array (RGB)."""
        try:
            image_data = base64.b64decode(base64_str)
            image = Image.open(io.BytesIO(image_data))
            image_rgb = image.convert("RGB")
            return cv2.cvtColor(np.array(image_rgb), cv2.COLOR_RGB2BGR)
        except Exception as e:
            raise ValueError(f"Invalid base64 image: {e}")
    
    def detect_face_landmarks(self, image_array: np.ndarray) -> Optional[Dict]:
        """
        Detect face landmarks using MediaPipe Face Mesh.
        
        Args:
            image_array: OpenCV format image array (BGR)
        
        Returns:
            Dictionary with landmark data or None
        """
        try:
            # Convert BGR to RGB for MediaPipe
            image_rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
            
            # Detect landmarks
            results = self.face_mesh.process(image_rgb)
            
            if not results.multi_face_landmarks:
                return None
            
            landmarks = results.multi_face_landmarks[0]
            h, w, _ = image_array.shape
            
            # Extract key landmarks
            landmark_data = {
                "total_landmarks": len(landmarks.landmark),
                "landmarks": [
                    {"x": lm.x, "y": lm.y, "z": lm.z} for lm in landmarks.landmark
                ],
            }
            
            return landmark_data
        
        except Exception as e:
            raise ValueError(f"Face landmark detection failed: {e}")
    
    def analyze_texture_features(self, image_array: np.ndarray) -> Dict[str, float]:
        """
        Analyze texture features to detect video playback or printed images.
        
        Args:
            image_array: OpenCV format image array (BGR)
        
        Returns:
            Dictionary with texture analysis results
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
            
            # Compute Laplacian (edge detection)
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_var = laplacian.var()
            
            # Compute Sobel edges
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edge_magnitude = np.sqrt(sobelx**2 + sobely**2)
            edge_mean = edge_magnitude.mean()
            
            # Compute local binary patterns (LBP) approximation
            # Calculate local variance
            local_var = cv2.GaussianBlur(gray, (5, 5), 0)
            local_var = cv2.calcHist([local_var], [0], None, [256], [0, 256])
            texture_variance = np.var(local_var)
            
            # High laplacian variance suggests natural liveness
            # Low variance suggests printed image or video
            liveness_texture_score = min(1.0, laplacian_var / 1000.0)
            
            return {
                "laplacian_variance": float(laplacian_var),
                "edge_mean": float(edge_mean),
                "texture_variance": float(texture_variance),
                "liveness_texture_score": float(liveness_texture_score),
            }
        
        except Exception as e:
            raise ValueError(f"Texture analysis failed: {e}")
    
    def analyze_face_motion(self, image_array: np.ndarray, prev_landmarks: Optional[Dict] = None) -> Dict:
        """
        Analyze face motion/presence of micro-expressions.
        
        Args:
            image_array: Current frame
            prev_landmarks: Previous frame landmarks for comparison
        
        Returns:
            Dictionary with motion analysis
        """
        try:
            landmarks = self.detect_face_landmarks(image_array)
            
            if landmarks is None:
                return {"has_face": False, "motion_score": 0.0}
            
            # If previous landmarks available, calculate movement
            if prev_landmarks:
                total_movement = 0.0
                for i, lm in enumerate(landmarks["landmarks"]):
                    prev_lm = prev_landmarks["landmarks"][i]
                    movement = np.sqrt(
                        (lm["x"] - prev_lm["x"])**2 +
                        (lm["y"] - prev_lm["y"])**2 +
                        (lm["z"] - prev_lm["z"])**2
                    )
                    total_movement += movement
                
                avg_movement = total_movement / len(landmarks["landmarks"])
                # Moderate movement is expected for real faces
                motion_score = min(1.0, avg_movement * 100)
            else:
                motion_score = 0.5  # Unknown without baseline
            
            return {
                "has_face": True,
                "motion_score": float(motion_score),
                "landmark_count": landmarks["total_landmarks"],
            }
        
        except Exception as e:
            return {"has_face": False, "motion_score": 0.0, "error": str(e)}
    
    def detect_blink_patterns(self, image_array: np.ndarray) -> Dict[str, float]:
        """
        Detect eye blink patterns (requires video sequence, but approximated from single image).
        
        Args:
            image_array: Single frame image
        
        Returns:
            Dictionary with blink detection approximation
        """
        try:
            landmarks = self.detect_face_landmarks(image_array)
            
            if landmarks is None:
                return {"blink_probability": 0.0}
            
            # MediaPipe face landmarks: eyes are at specific indices
            # Left eye: 33, 133, 160, 158, 133
            # Right eye: 362, 263, 387, 385, 263
            
            lms = landmarks["landmarks"]
            
            # Calculate eye aspect ratio
            def eye_aspect_ratio(eye_indices):
                p1 = np.array([lms[eye_indices[0]]["x"], lms[eye_indices[0]]["y"]])
                p2 = np.array([lms[eye_indices[1]]["x"], lms[eye_indices[1]]["y"]])
                p3 = np.array([lms[eye_indices[2]]["x"], lms[eye_indices[2]]["y"]])
                p4 = np.array([lms[eye_indices[3]]["x"], lms[eye_indices[3]]["y"]])
                p5 = np.array([lms[eye_indices[4]]["x"], lms[eye_indices[4]]["y"]])
                p6 = np.array([lms[eye_indices[5]]["x"], lms[eye_indices[5]]["y"]])
                
                a = np.linalg.norm(p2 - p6)
                b = np.linalg.norm(p3 - p5)
                c = np.linalg.norm(p1 - p4)
                
                return (a + b) / (2.0 * c) if c > 0 else 0.0
            
            left_ear = eye_aspect_ratio([33, 133, 160, 158, 133, 33])
            right_ear = eye_aspect_ratio([362, 263, 387, 385, 263, 362])
            avg_ear = (left_ear + right_ear) / 2.0
            
            # Blink is detected when EAR < threshold
            blink_threshold = 0.2
            blink_probability = 1.0 if avg_ear < blink_threshold else 0.0
            
            return {
                "left_eye_aspect_ratio": float(left_ear),
                "right_eye_aspect_ratio": float(right_ear),
                "average_eye_aspect_ratio": float(avg_ear),
                "blink_probability": float(blink_probability),
            }
        
        except Exception as e:
            return {"blink_probability": 0.0, "error": str(e)}
    
    def comprehensive_liveness_check(self, image_base64: str) -> Dict[str, any]:
        """
        Comprehensive liveness detection combining multiple methods.
        
        Args:
            image_base64: Base64 encoded image
        
        Returns:
            Dictionary with liveness assessment
        """
        try:
            image_array = self._base64_to_array(image_base64)
            
            # Run all detection methods
            texture_analysis = self.analyze_texture_features(image_array)
            blink_analysis = self.detect_blink_patterns(image_array)
            motion_analysis = self.analyze_face_motion(image_array)
            
            # Compute liveness score
            # Combine multiple signals
            liveness_score = (
                0.3 * texture_analysis["liveness_texture_score"] +
                0.3 * min(1.0, blink_analysis.get("average_eye_aspect_ratio", 0.3) * 3) +
                0.2 * motion_analysis.get("motion_score", 0.5) +
                0.2 * (1.0 if motion_analysis["has_face"] else 0.0)
            )
            
            # Risk assessment
            if liveness_score > 0.8:
                liveness_risk = "low"
                liveness_status = "likely_genuine"
            elif liveness_score > 0.6:
                liveness_risk = "medium"
                liveness_status = "uncertain"
            elif liveness_score > 0.4:
                liveness_risk = "high"
                liveness_status = "likely_synthetic"
            else:
                liveness_risk = "critical"
                liveness_status = "definitely_fake"
            
            return {
                "liveness_score": float(liveness_score),
                "liveness_status": liveness_status,
                "liveness_risk": liveness_risk,
                "texture_analysis": texture_analysis,
                "blink_analysis": blink_analysis,
                "motion_analysis": motion_analysis,
                "confidence": 0.85,
            }
        
        except Exception as e:
            return {
                "liveness_score": 0.0,
                "liveness_status": "error",
                "liveness_risk": "unknown",
                "error": str(e),
            }


# Global instance
_liveness_engine: Optional[LivenessDetectionEngine] = None


def get_liveness_detection_engine() -> LivenessDetectionEngine:
    """Get or initialize liveness detection engine (singleton pattern)."""
    global _liveness_engine
    
    if _liveness_engine is None:
        _liveness_engine = LivenessDetectionEngine()
    
    return _liveness_engine
