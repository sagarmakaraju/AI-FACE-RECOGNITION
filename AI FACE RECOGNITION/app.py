import os
import uuid
import datetime
import base64
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from werkzeug.utils import secure_filename

import config
import database
from modules.ocr_engine import OCREngine
from modules.tampering_detector import TamperingDetector
from modules.face_verifier import FaceVerifier
from modules.risk_engine import RiskEngine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
app.config['SECRET_KEY'] = config.SECRET_KEY

# Ensure directories exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(config.MODELS_FOLDER, exist_ok=True)
os.makedirs(config.SAMPLES_FOLDER, exist_ok=True)

# Initialize database
database.init_db()

# Initialize AI Engines (singleton instances)
print("Initializing AI Pipelines...")
ocr_engine = OCREngine()
tampering_detector = TamperingDetector()
face_verifier = FaceVerifier()
risk_engine = RiskEngine()
print("All AI Engines initialized successfully!")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def save_base64_image(base64_data, prefix="webcam"):
    """Saves a base64 encoded image string to uploads directory"""
    if not base64_data:
        return None
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    
    img_bytes = base64.b64decode(base64_data)
    filename = f"{prefix}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(filepath, 'wb') as f:
        f.write(img_bytes)
    return filename, filepath

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = database.get_screening_stats()
    return jsonify(stats)

@app.route('/api/samples', methods=['GET'])
def get_samples():
    samples = [
        {
            "id": "clean_aadhaar",
            "name": "1. Clean Aadhaar Card",
            "category": "Normal Document",
            "expected_risk": "LOW",
            "description": "Authentic Aadhaar Card with matching selfie portrait and valid Verhoeff number.",
            "doc_url": "/static/samples/sample_clean_aadhaar.jpg",
            "selfie_url": "/static/samples/selfie_person1.jpg"
        },
        {
            "id": "tampered_pan",
            "name": "2. Tampered PAN Card",
            "category": "Fraud / Tampering",
            "expected_risk": "HIGH / MEDIUM",
            "description": "PAN card with digitally spliced/tampered number exhibiting JPEG compression artifacts.",
            "doc_url": "/static/samples/sample_tampered_pan.jpg",
            "selfie_url": "/static/samples/selfie_person2.jpg"
        },
        {
            "id": "face_mismatch",
            "name": "3. Biometric Face Mismatch",
            "category": "Impersonation Attempt",
            "expected_risk": "HIGH",
            "description": "Genuine passport presented with completely different applicant selfie photo.",
            "doc_url": "/static/samples/sample_face_mismatch_doc.jpg",
            "selfie_url": "/static/samples/selfie_mismatch.jpg"
        },
        {
            "id": "poor_quality",
            "name": "4. Poor Quality / Blurred ID",
            "category": "Degraded Capture",
            "expected_risk": "MEDIUM / HIGH",
            "description": "Heavily blurred, underexposed ID triggering manual review safeguards.",
            "doc_url": "/static/samples/sample_poor_quality_dl.jpg",
            "selfie_url": "/static/samples/selfie_person4.jpg"
        }
    ]
    return jsonify(samples)

@app.route('/api/verify', methods=['POST'])
def verify_pipeline():
    try:
        doc_filepath = None
        selfie_filepath = None
        doc_filename = None
        selfie_filename = None
        
        timestamp_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        unique_prefix = f"{timestamp_str}_{uuid.uuid4().hex[:6]}"
        
        # Check if sample ID was selected
        sample_id = request.form.get('sample_id')
        if sample_id:
            sample_map = {
                "clean_aadhaar": ("static/samples/sample_clean_aadhaar.jpg", "static/samples/selfie_person1.jpg"),
                "tampered_pan": ("static/samples/sample_tampered_pan.jpg", "static/samples/selfie_person2.jpg"),
                "face_mismatch": ("static/samples/sample_face_mismatch_doc.jpg", "static/samples/selfie_mismatch.jpg"),
                "poor_quality": ("static/samples/sample_poor_quality_dl.jpg", "static/samples/selfie_person4.jpg")
            }
            if sample_id in sample_map:
                src_doc, src_selfie = sample_map[sample_id]
                
                # Copy to uploads
                doc_filename = f"doc_{unique_prefix}.jpg"
                selfie_filename = f"selfie_{unique_prefix}.jpg"
                doc_filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc_filename)
                selfie_filepath = os.path.join(app.config['UPLOAD_FOLDER'], selfie_filename)
                
                with open(src_doc, 'rb') as f_in, open(doc_filepath, 'wb') as f_out:
                    f_out.write(f_in.read())
                with open(src_selfie, 'rb') as f_in, open(selfie_filepath, 'wb') as f_out:
                    f_out.write(f_in.read())
        
        # Check document file upload
        if not doc_filepath:
            if 'document_file' in request.files and request.files['document_file'].filename != '':
                file = request.files['document_file']
                if allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    doc_filename = f"doc_{unique_prefix}.{ext}"
                    doc_filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc_filename)
                    file.save(doc_filepath)
            elif request.form.get('document_base64'):
                doc_filename, doc_filepath = save_base64_image(request.form.get('document_base64'), prefix=f"doc_{unique_prefix}")
                
        # Check selfie file upload / webcam
        if not selfie_filepath:
            if 'selfie_file' in request.files and request.files['selfie_file'].filename != '':
                file = request.files['selfie_file']
                if allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    selfie_filename = f"selfie_{unique_prefix}.{ext}"
                    selfie_filepath = os.path.join(app.config['UPLOAD_FOLDER'], selfie_filename)
                    file.save(selfie_filepath)
            elif request.form.get('selfie_base64'):
                selfie_filename, selfie_filepath = save_base64_image(request.form.get('selfie_base64'), prefix=f"selfie_{unique_prefix}")

        if not doc_filepath or not os.path.exists(doc_filepath):
            return jsonify({"status": "error", "message": "Identity Document image is required."}), 400
            
        if not selfie_filepath or not os.path.exists(selfie_filepath):
            return jsonify({"status": "error", "message": "Live Selfie / Person photo is required."}), 400
            
        # File paths for generated artifacts
        heatmap_filename = f"forensic_{unique_prefix}.jpg"
        heatmap_filepath = os.path.join(app.config['UPLOAD_FOLDER'], heatmap_filename)
        
        ocr_annotated_filename = f"ocr_box_{unique_prefix}.jpg"
        ocr_annotated_filepath = os.path.join(app.config['UPLOAD_FOLDER'], ocr_annotated_filename)
        
        doc_crop_filename = f"doc_face_{unique_prefix}.jpg"
        doc_crop_filepath = os.path.join(app.config['UPLOAD_FOLDER'], doc_crop_filename)
        
        selfie_crop_filename = f"selfie_face_{unique_prefix}.jpg"
        selfie_crop_filepath = os.path.join(app.config['UPLOAD_FOLDER'], selfie_crop_filename)
        
        # -------------------------------------------------------------
        # STEP 1: OCR Extraction Engine
        # -------------------------------------------------------------
        ocr_result = ocr_engine.process(doc_filepath, annotated_output_path=ocr_annotated_filepath)
        
        # -------------------------------------------------------------
        # STEP 2: Forensic Tampering Detection Engine
        # -------------------------------------------------------------
        tampering_result = tampering_detector.analyze(doc_filepath, heatmap_output_path=heatmap_filepath)
        
        # -------------------------------------------------------------
        # STEP 3: Deep Learning Face Verification Engine
        # -------------------------------------------------------------
        face_result = face_verifier.verify(
            doc_filepath,
            selfie_filepath,
            doc_crop_out=doc_crop_filepath,
            selfie_crop_out=selfie_crop_filepath
        )
        
        # -------------------------------------------------------------
        # STEP 4: Validation & Composite Risk Engine
        # -------------------------------------------------------------
        validation_result = risk_engine.validate_document(ocr_result)
        risk_result = risk_engine.assess_risk(ocr_result, tampering_result, face_result, validation_result)
        
        # Screening ID
        screening_id = f"SCR-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
        
        # Package full result
        full_response = {
            "status": "success",
            "screening_id": screening_id,
            "timestamp": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "document_image": doc_filename,
            "selfie_image": selfie_filename,
            "ocr": ocr_result,
            "tampering": tampering_result,
            "face_verification": face_result,
            "validation": validation_result,
            "risk_assessment": risk_result
        }
        
        # Save to SQLite database
        database.save_screening(full_response)
        
        return jsonify(full_response)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Verification failed: {str(e)}"}), 500

@app.route('/api/screenings', methods=['GET'])
def get_screenings():
    search = request.args.get('search', '').strip() or None
    risk = request.args.get('risk', '').strip() or None
    doc_type = request.args.get('doc_type', '').strip() or None
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    records = database.get_all_screenings(limit=limit, offset=offset, search=search, risk_filter=risk, doc_type_filter=doc_type)
    return jsonify(records)

@app.route('/api/screening/<screening_id>', methods=['GET'])
def get_screening_detail(screening_id):
    record = database.get_screening_by_id(screening_id)
    if record:
        return jsonify({"status": "success", "data": record})
    return jsonify({"status": "error", "message": "Screening record not found"}), 404

@app.route('/api/screening/<screening_id>', methods=['DELETE'])
def delete_screening_record(screening_id):
    deleted = database.delete_screening(screening_id)
    if deleted:
        return jsonify({"status": "success", "message": "Screening deleted successfully"})
    return jsonify({"status": "error", "message": "Could not delete record"}), 400

if __name__ == '__main__':
    print("Starting SIH26188 AI Face Recognition & Document Verification Server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
