# model_loader.py
import insightface
from insightface.app import FaceAnalysis

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