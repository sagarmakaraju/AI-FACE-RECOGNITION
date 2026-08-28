# VerifAI — AI Face Recognition & Document Fraud Verification System
**Smart India Hackathon (SIH26188)**

VERIFAI is an end-to-end AI document verification and anti-fraud screening platform combining Deep Learning OCR, Image Tampering & Compression Forensics (ELA), Facial Biometric Verification (YuNet + SFace), and an Explainable AI (XAI) Multi-Factor Risk Assessment Engine.

---

## 🌟 Key Features

- 🔍 **RapidOCR Deep Learning Engine**: High-accuracy text detection & field extraction for Aadhaar, PAN, Passport, Driving License, and Voter ID.
- 🛡️ **Forensic Tampering & ELA Detector**: Error Level Analysis (ELA), 16x16 block spatial noise variance analysis, and Sobel edge gradient anomaly detection with false-color heatmaps (`cv2.COLORMAP_JET`).
- 👤 **Facial Biometric Verification**: OpenCV YuNet neural face detection & SFace 128-D embedding extraction with cosine similarity matching and side-by-side face comparison crops.
- 🧠 **Explainable Multi-Factor Risk Engine**: Verhoeff checksum algorithm for 12-digit Aadhaar, PAN 4th-char entity validation, date sanity checks, and weighted composite risk scoring (0-100) with explainable audit trails.
- 💻 **Modern Web Dashboard & History**: Glassmorphic UI with Tailwind CSS, Live WebRTC Webcam capture, 1-Click Quick Demo Suite, and SQLite screening history database with search, filter, and JSON export.

---

## 📁 Project Structure

```
c:\AI FACE RECOGNITION\
├── app.py                      # Flask Application & REST API (Member 1)
├── config.py                   # Configuration & Risk Weights (Member 1)
├── database.py                 # SQLite Database Manager (Member 6 / 1)
├── modules/
│   ├── ocr_engine.py           # RapidOCR & Entity Extractor (Member 2)
│   ├── tampering_detector.py   # ELA & Noise Forensics (Member 3)
│   ├── face_verifier.py        # YuNet & SFace Biometrics (Member 4)
│   └── risk_engine.py          # Verhoeff & Composite Risk Engine (Member 5)
├── models/
│   ├── face_detection_yunet_2023mar.onnx
│   └── face_recognition_sface_2021dec.onnx
├── static/
│   ├── css/styles.css          # Styling & Animations
│   ├── js/app.js               # Frontend Controller & WebRTC
│   └── samples/                # Pre-loaded Demo Test Suite
├── templates/
│   ├── base.html               # Base layout & Navbar
│   ├── index.html              # Verification Dashboard
│   └── history.html            # Screening Audit Trail
├── tests/
│   └── test_all_modules.py     # Automated Unit & Integration Tests
├── scripts/
│   └── generate_sample_data.py # Demo Test Generator
├── SIH_PRESENTATION_GUIDE.md   # Presentation & Demo Script
└── README.md
```

---

## ⚡ Quick Start

```powershell
# 1. Install dependencies
pip install flask opencv-python pillow numpy onnxruntime rapidocr-onnxruntime scikit-image requests

# 2. Generate demo sample test cases
python scripts/generate_sample_data.py

# 3. Run all automated tests
python -m unittest tests/test_all_modules.py

# 4. Start the application
python app.py
```

Visit **`http://127.0.0.1:5000`** in your browser.
