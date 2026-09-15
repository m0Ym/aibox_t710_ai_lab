import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Import FaceProcessor from file to avoid importing top-level `panel.py` (name collision)
import importlib.util
face_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'panel', 'face.py'))
spec = importlib.util.spec_from_file_location("panel_face", face_path)
face_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(face_mod)
FaceProcessor = face_mod.FaceProcessor


def test_face_processor_with_dummy_detector():
    class DummyDetector:
        def __init__(self, face_model_dir, landmark_model_dir):
            # record that ctor received paths
            self._paths = (face_model_dir, landmark_model_dir)
            self.detector = self

        def render(self, frame, face_res=None, threshold=None):
            # If called as detector.render(frame) -> return faces
            if face_res is None:
                return [{'box': [0, 0, 10, 10]}]
            # If called as render(frame, face_res, threshold) -> return landmarks
            return [{'points': [(1, 2)]}]

        def drawBox(self, frame, landmark_res):
            return 'frame_processed'

    fp = FaceProcessor('face_model_dir', 'landmark_dir', detector_cls=DummyDetector)
    out = fp.process('frame')
    assert out == 'frame_processed'