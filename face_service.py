# face_service.py
import numpy as np
from errors import NoFaceDetectedError, MultipleFacesError


class FaceService:
    def __init__(self, model_app):
        self.app = model_app  # the FaceAnalysis instance from model_loader

    def extract_embedding(self, image: np.ndarray, expect_single: bool = True) -> np.ndarray:
        faces = self.app.get(image)  # runs detection + alignment + embedding internally

        if len(faces) == 0:
            raise NoFaceDetectedError("No face found in image")
        if expect_single and len(faces) > 1:
            raise MultipleFacesError(f"Expected 1 face, found {len(faces)}")

        face = faces[0]
        embedding = face.embedding  # 512-d vector, already L2-normalizable
        return embedding / np.linalg.norm(embedding)  # normalize for cosine sim via FAISS IndexFlatIP