# SIH26188 — AI Face Recognition & Document Fraud Verification System
## Complete Hackathon Presentation, Demo Script & Technical Architecture

---

## 🏆 Project Overview
**VERIFAI (SIH26188)** is a multi-modal AI Identity Verification & Anti-Fraud Screening platform designed to combat document manipulation, identity forgery, impersonation attacks, and digital tampering across national identity documents (Aadhaar, PAN, Passport, Driving License, Voter ID).

---

## 👥 24-Hour Task Division & Deliverables Matrix

| Member | Role | Key Deliverables & Implemented Architecture |
| :--- | :--- | :--- |
| **👤 Member 1** | **Backend & Integration** | Flask web framework, REST API (`/api/verify`, `/api/screenings`, `/api/stats`, `/api/samples`), pipeline orchestrator, error handling, session & storage manager. |
| **👤 Member 2** | **OCR & Entity Extraction** | RapidOCR deep learning ONNX engine, CLAHE & bilateral preprocessing, document classifier (Aadhaar/PAN/Passport/DL), Name/DOB/Doc-Number/Expiry extraction, per-field confidence scoring. |
| **👤 Member 3** | **Tampering Detection** | Error Level Analysis (ELA) JPEG difference analyzer, 16x16 block spatial noise variance inconsistency, Sobel boundary gradient anomalies, colorized forensic heatmap generation (`cv2.COLORMAP_JET`), tampering scoring (0-100). |
| **👤 Member 4** | **Face Verification** | YuNet ONNX face detector, SFace 128-D facial feature embedding extractor (`cv2.FaceRecognizerSF`), Cosine Similarity & L2 Euclidean distance calculator, multi-face warning, portrait cropping. |
| **👤 Member 5** | **Validation & Risk Engine** | Verhoeff algorithm for 12-digit Aadhaar, PAN format & entity type validation (P/C/H/F/A), age & expiry checks, multi-factor composite risk scoring ($0.20 \text{ OCR} + 0.20 \text{ Val} + 0.30 \text{ Tamper} + 0.30 \text{ Face}$), explainable AI (XAI) reason generator. |
| **👤 Member 6** | **Frontend & Database** | Tailwind CSS glassmorphic dashboard, dual drag-and-drop upload zone, Live Webcam capture (WebRTC), 1-click Quick Demo Suite, comprehensive results cards with ELA heatmap viewer, SQLite screening audit database with search/filter/export. |

---

## 🚀 Live Demo Script for Judges

### **Step 1: Introduction & System Startup (30 seconds)**
- Open browser at `http://127.0.0.1:5000`.
- Point out the clean **VerifAI Dashboard** with live statistics counters (Total Screenings, Low Risk, Medium Review, High Risk Fraud).

### **Step 2: Scenario 1 — Clean Authentic Aadhaar Card (45 seconds)**
- Click **"1. Clean Aadhaar"** in the Quick Demo bar.
- Click **"Run Complete AI Verification Pipeline"**.
- Point out:
  - **Verdict:** `LOW RISK (SAFE) — VERIFIED / APPROVED` (Risk Score: ~12-22 / 100).
  - **OCR:** Document correctly identified as *Aadhaar Card*, Name *ARUN KUMAR VERMA*, Number *5489 2174 9633*, DOB *14/11/1992*.
  - **Face Biometrics:** YuNet detected face, SFace similarity match verified (>80%).
  - **Forensics:** ELA heatmap is uniform blue/cool with 0% anomaly.
  - **Validation:** Verhoeff checksum verified on 12-digit Aadhaar.

### **Step 3: Scenario 2 — Digital Forgery & Tampered PAN Card (45 seconds)**
- Click **"2. Tampered PAN"** in the Quick Demo bar.
- Click **"Run Complete AI Verification Pipeline"**.
- Point out:
  - **Verdict:** `HIGH / MEDIUM RISK` with Forensic Tampering Alert.
  - **Forensic Heatmap:** The ELA viewer clearly lights up **red/yellow hotspots** around the modified PAN number where compression distortion and high-frequency noise variance occurred.
  - **Explainable Reasons:** Clearly lists *"Localized JPEG compression anomaly detected"*.

### **Step 4: Scenario 3 — Biometric Impersonation / Face Mismatch (45 seconds)**
- Click **"3. Face Mismatch"** in the Quick Demo bar.
- Click **"Run Complete AI Verification Pipeline"**.
- Point out:
  - **Verdict:** `HIGH RISK — REJECTED / SUSPECT FRAUD`.
  - **Biometrics:** Side-by-side face comparison shows applicant selfie does not match document portrait.
  - SFace cosine similarity is below threshold.

### **Step 5: Scenario 4 — Live Webcam Test & Audit Trail (45 seconds)**
- Click **"Live Webcam"** button to capture live selfie from camera.
- Navigate to **"Screening History"** (`/history`).
- Show the immutable SQLite audit trail with search, risk filters, detailed inspection modal, and JSON export.

---

## 📊 Presentation Slide Outline (Ready for PPT)

- **Slide 1:** Title Slide (SIH26188 — VERIFAI: AI-Powered Multi-Modal Identity & Document Fraud Detection)
- **Slide 2:** Problem Statement (Identity Theft, Forged IDs, Deepfakes, Financial Fraud)
- **Slide 3:** Proposed Solution & Multi-Layer Defense Architecture
- **Slide 4:** Deep Learning OCR & Entity Parsing Engine (RapidOCR + Context Heuristics)
- **Slide 5:** Image Forensics & Tampering Detection (ELA + Spatial Noise Variance + Gradient Discontinuity)
- **Slide 6:** Biometric Facial Verification (YuNet Face Detection + SFace 128-D Embeddings)
- **Slide 7:** Multi-Factor Risk Engine & Explainable AI (XAI)
- **Slide 8:** Live System Architecture & Tech Stack (Flask, SQLite, Tailwind, OpenCV, ONNX)
- **Slide 9:** Scalability, Security & Production Deployment Roadmap
- **Slide 10:** Conclusion & Team Contributions

---

## 🛠️ How to Run the Application

```powershell
# 1. Generate demo sample test cases
python scripts/generate_sample_data.py

# 2. Run automated test suite
python -m unittest tests/test_all_modules.py

# 3. Start Flask Web Server
python app.py
```
Open **`http://127.0.0.1:5000`** in any modern web browser.
