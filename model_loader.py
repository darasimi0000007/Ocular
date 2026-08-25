# model_loader.py
import insightface
from insightface.app import FaceAnalysis
import numpy as np

def load_face_model(ctx_id: int = -1, det_size: tuple = (640, 640)):
    """
    ctx_id: -1 for CPU, 0+ for GPU device index
    det_size: input resolution for RetinaFace detector
    """
    app = FaceAnalysis(
        name="buffalo_l",  # bundle: RetinaFace + ArcFace (r100)
        providers=["CPUExecutionProvider"]  # or CUDAExecutionProvider
    )
    app.prepare(ctx_id=ctx_id, det_size=det_size)
    return app



def extract_embedding(image_bgr: np.ndarray) -> np.ndarray | None:
    """
    Returns a single L2-normalized 512-dim embedding for the most
    prominent face in the image, or None if no face detected.
    """
    faces = load_face_model().get(image_bgr)
    if not faces:
        return None

    # naive "pick largest face" policy -- fine for enrollment/portfolio scope
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    embedding = face.embedding
    norm = np.linalg.norm(embedding)
    return embedding / norm if norm > 0 else embedding