"""Face processor wrapper for FaceKeyPoint detector.
Provides a small, testable adapter around faceLandmark.FaceKeyPoint.
"""
from typing import Any


class FaceProcessor:
    def __init__(self, face_model_dir: str, landmark_model_dir: str, threshold: float = 0.5, detector_cls=None):
        """Initialize face processor.
        detector_cls: optional class to use instead of faceLandmark.FaceKeyPoint (useful for tests).
        """
        if detector_cls is None:
            try:
                from faceLandmark import FaceKeyPoint as _FKP
            except Exception:
                _FKP = None
            detector_cls = _FKP

        if detector_cls is None:
            raise RuntimeError("FaceKeyPoint detector not available")

        self.detector = detector_cls(face_model_dir, landmark_model_dir)
        self.threshold = threshold

    def process(self, frame: Any):
        """Run detection + landmark and draw boxes on frame. Returns new frame."""
        face_res = self.detector.detector.render(frame)
        landmark_res = self.detector.render(frame, face_res, self.threshold)
        frame_with_landmark = self.detector.drawBox(frame, landmark_res)
        return frame_with_landmark
