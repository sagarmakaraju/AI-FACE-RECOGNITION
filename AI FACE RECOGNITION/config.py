import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Upload and Storage Folders
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
MODELS_FOLDER = os.path.join(BASE_DIR, 'models')
SAMPLES_FOLDER = os.path.join(BASE_DIR, 'static', 'samples')
DATABASE_PATH = os.path.join(BASE_DIR, 'screenings.db')

# Model File Paths
YUNET_MODEL_PATH = os.path.join(MODELS_FOLDER, 'face_detection_yunet_2023mar.onnx')
SFACE_MODEL_PATH = os.path.join(MODELS_FOLDER, 'face_recognition_sface_2021dec.onnx')

# Upload Constraints
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}

# Face Verification Thresholds
FACE_MATCH_THRESHOLD = 0.65  # Cosine similarity >= 65% is considered a match
FACE_UNCERTAIN_THRESHOLD = 0.50

# Tampering Detection Thresholds
TAMPERING_SUSPICIOUS_THRESHOLD = 50.0
TAMPERING_REVIEW_THRESHOLD = 25.0

# Risk Engine Thresholds (Composite Risk Score 0 - 100)
RISK_LOW_MAX = 25.0
RISK_MEDIUM_MAX = 55.0

# Composite Risk Engine Weights (Sum = 1.0)
RISK_WEIGHTS = {
    'ocr_confidence': 0.20,
    'field_validation': 0.20,
    'tampering': 0.30,
    'face_verification': 0.30
}

# Flask Settings
SECRET_KEY = 'sih26188-ai-face-verification-secret-key'
DEBUG = True