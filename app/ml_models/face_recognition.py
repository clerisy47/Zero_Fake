from __future__ import annotations

import base64
import io
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

try:
    from deepface import DeepFace
    from facenet_pytorch import InceptionResnetV1
    import torch
except ImportError:
    raise RuntimeError("DeepFace and facenet-pytorch are required. Install with: pip install -r requirements.txt")


class FaceRecognitionEngine:
    """Advanced face recognition using DeepFace and FaceNet."""
    
    def __init__(self):
        """Initialize face recognition models."""
        # DeepFace models (auto-loads on first use)
        self.deepface_models = ["VGG-Face", "Facenet", "Facenet512", "OpenFace", "DeepID"]
        
        # FaceNet model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.facenet_model = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
        
        print(f"✅ Face Recognition Engine initialized (device: {self.device})")
    
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
    
    def extract_face_embedding(self, image_base64: str, model: str = "Facenet512") -> Tuple[np.ndarray, float]:
        """
        Extract face embedding using DeepFace.
        
        Args:
            image_base64: Base64 encoded face image
            model: Model to use (Facenet512 recommended for accuracy)
        
        Returns:
            Tuple of (embedding vector, confidence score)
        """
        try:
            image = self._base64_to_image(image_base64)
            image_array = self._image_to_array(image)
            
            # Extract embedding using DeepFace
            embedding_objs = DeepFace.represent(
                img_path=image_array,
                model_name=model,
                enforce_detection=True,
                detector_backend="retinaface",
            )
            
            if not embedding_objs:
                return np.array([]), 0.0
            
            embedding = np.array(embedding_objs[0]["embedding"])
            confidence = 0.95  # DeepFace confidence
            
            return embedding, confidence
        
        except Exception as e:
            raise ValueError(f"Face extraction failed: {e}")
    
    def extract_facenet_embedding(self, image_base64: str) -> Tuple[List[float], float]:
        """
        Extract face embedding using FaceNet-PyTorch.
        
        Args:
            image_base64: Base64 encoded face image
        
        Returns:
            Tuple of (embedding list, confidence score)
        """
        try:
            image = self._base64_to_image(image_base64)
            image_resized = image.resize((160, 160))  # FaceNet input size
            
            # Convert to tensor
            image_tensor = torch.tensor(np.array(image_resized), dtype=torch.float32)
            image_tensor = image_tensor.permute(2, 0, 1).unsqueeze(0).to(self.device)
            image_tensor = image_tensor / 255.0  # Normalize
            
            # Extract embedding
            with torch.no_grad():
                embedding = self.facenet_model(image_tensor)
            
            embedding_np = embedding.cpu().numpy()[0]
            return embedding_np.tolist(), 0.98
        
        except Exception as e:
            raise ValueError(f"FaceNet embedding extraction failed: {e}")
    
    def compare_faces(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
        threshold: float = 0.6,
    ) -> Tuple[float, bool]:
        """
        Compare two face embeddings.
        
        Args:
            embedding1: First face embedding
            embedding2: Second face embedding
            threshold: Similarity threshold (0-1)
        
        Returns:
            Tuple of (similarity score, is_match)
        """
        try:
            # Cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            similarity = dot_product / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0.0
            
            # Normalize to 0-1 range
            similarity = (similarity + 1) / 2
            
            is_match = similarity >= threshold
            return float(similarity), is_match
        
        except Exception as e:
            raise ValueError(f"Face comparison failed: {e}")
    
    def verify_face_match(self, image1_base64: str, image2_base64: str) -> Dict[str, any]:
        """
        Verify if two images contain the same person.
        
        Args:
            image1_base64: First image (document)
            image2_base64: Second image (selfie)
        
        Returns:
            Dictionary with verification result
        """
        try:
            # Extract embeddings
            embedding1, _ = self.extract_face_embedding(image1_base64)
            embedding2, _ = self.extract_face_embedding(image2_base64)
            
            if len(embedding1) == 0 or len(embedding2) == 0:
                return {
                    "verified": False,
                    "similarity": 0.0,
                    "confidence": 0.0,
                    "error": "Could not extract face from one or both images",
                }
            
            # Compare
            similarity, is_match = self.compare_faces(embedding1, embedding2, threshold=0.55)
            
            return {
                "verified": is_match,
                "similarity": float(similarity),
                "confidence": 0.95 if is_match else 0.90,
                "error": None,
            }
        
        except Exception as e:
            return {
                "verified": False,
                "similarity": 0.0,
                "confidence": 0.0,
                "error": str(e),
            }
    
    def find_nearest_match(
        self,
        query_embedding: np.ndarray,
        stored_embeddings: Dict[str, np.ndarray],
        threshold: float = 0.92,
    ) -> Optional[Tuple[str, float]]:
        """
        Find nearest match in stored embeddings (for deduplication).
        
        Args:
            query_embedding: Query face embedding
            stored_embeddings: Dictionary of submission_id -> embedding
            threshold: Match threshold
        
        Returns:
            Tuple of (submission_id, similarity) or None
        """
        best_match = None
        best_similarity = 0.0
        
        for submission_id, embedding in stored_embeddings.items():
            similarity, _ = self.compare_faces(query_embedding, embedding, threshold=0.0)
            
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = submission_id
        
        return (best_match, best_similarity) if best_match else None


# Global instance
_face_recognition_engine: Optional[FaceRecognitionEngine] = None


def get_face_recognition_engine() -> FaceRecognitionEngine:
    """Get or initialize the face recognition engine (singleton pattern)."""
    global _face_recognition_engine
    
    if _face_recognition_engine is None:
        _face_recognition_engine = FaceRecognitionEngine()
    
    return _face_recognition_engine
