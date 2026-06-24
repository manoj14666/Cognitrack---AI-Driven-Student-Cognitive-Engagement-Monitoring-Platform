import cv2
import numpy as np
from deepface import DeepFace

class AuthVerifier:
    def __init__(self):
        # Facenet is accurate and relatively fast
        self.model_name = "Facenet"
        # Standard threshold for Facenet cosine distance is around 0.40
        self.threshold = 0.40 
        
        # Pre-build the model to load weights into memory once
        try:
            DeepFace.build_model(self.model_name)
            print(f"AuthVerifier initialized with {self.model_name}")
        except Exception as e:
            print(f"Warning: Could not pre-build model: {e}")

    def cosine_distance(self, a, b):
        a = np.array(a)
        b = np.array(b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 1.0
        return 1.0 - (np.dot(a, b) / (norm_a * norm_b))

    def compute_embedding(self, image):
        """
        Compute embedding for a single image.
        Image can be a numpy array (cv2 frame).
        """
        try:
            # enforce_detection=True ensures we only extract if a face is found
            result = DeepFace.represent(img_path=image, model_name=self.model_name, enforce_detection=True)
            if len(result) > 0:
                if isinstance(result, list) and isinstance(result[0], dict):
                    return result[0]["embedding"]
                elif isinstance(result, list) and (isinstance(result[0], float) or type(result[0]).__name__ == 'float32' or type(result[0]).__name__ == 'float64'):
                    return result
                elif isinstance(result, dict) and "embedding" in result:
                    return result["embedding"]
                else:
                    return result # fallback
        except Exception as e:
            print(f"Error computing embedding: {e}")
            return None
        return None

    def compute_average_embedding(self, images):
        """
        Compute average embedding for multiple images (numpy arrays).
        """
        embeddings = []
        for img in images:
            emb = self.compute_embedding(img)
            if emb is not None:
                embeddings.append(emb)
        
        if not embeddings:
            return None
            
        avg_embedding = np.mean(embeddings, axis=0)
        return avg_embedding.tolist()

    def verify_identity(self, frame, stored_embedding):
        """
        Verify the face in 'frame' against 'stored_embedding'.
        Returns: tuple(status, distance)
        Status: "Present", "Imposter Detected", "No Face Detected"
        """
        if not stored_embedding:
            # If student has no stored embedding, we can't verify. Default to Present to not block them
            return "Present", 0.0

        try:
            result = DeepFace.represent(img_path=frame, model_name=self.model_name, enforce_detection=True)
            
            if len(result) == 0:
                return "No Face Detected", 0.0
                
            if isinstance(result, list) and isinstance(result[0], dict):
                live_embedding = result[0]["embedding"]
            elif isinstance(result, list) and (isinstance(result[0], float) or type(result[0]).__name__ == 'float32' or type(result[0]).__name__ == 'float64'):
                live_embedding = result
            elif isinstance(result, dict) and "embedding" in result:
                live_embedding = result["embedding"]
            else:
                live_embedding = result
            
            # Calculate cosine distance
            distance = self.cosine_distance(stored_embedding, live_embedding)
            
            if distance <= self.threshold:
                return "Present", float(distance)
            else:
                return "Imposter Detected", float(distance)
                
        except ValueError:
            # DeepFace raises ValueError if no face is detected
            return "No Face Detected", 0.0
        except Exception as e:
            print(f"Verification error: {e}")
            return "No Face Detected", 0.0
