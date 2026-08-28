import sqlite3
import json
import uuid
import datetime
import os
import config

def get_db_connection():
    db_dir = os.path.dirname(config.DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            screening_id TEXT UNIQUE NOT NULL,
            timestamp TEXT NOT NULL,
            document_filename TEXT,
            selfie_filename TEXT,
            forensic_heatmap_filename TEXT,
            document_face_crop TEXT,
            selfie_face_crop TEXT,
            document_type TEXT,
            extracted_name TEXT,
            extracted_dob TEXT,
            extracted_doc_number TEXT,
            extracted_expiry TEXT,
            ocr_confidence REAL,
            tampering_score REAL,
            tampering_classification TEXT,
            face_similarity REAL,
            face_match INTEGER,
            composite_risk_score REAL,
            risk_level TEXT,
            verdict TEXT,
            raw_ocr_json TEXT,
            tampering_details_json TEXT,
            face_details_json TEXT,
            validation_details_json TEXT,
            reasons_json TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_screening(result_data):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now_str = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    rand_suffix = uuid.uuid4().hex[:4].upper()
    screening_id = result_data.get('screening_id') or (f"SCR-{now_str}-{rand_suffix}")
    timestamp = result_data.get('timestamp') or datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    ocr = result_data.get('ocr', {})
    tampering = result_data.get('tampering', {})
    face = result_data.get('face_verification', {})
    validation = result_data.get('validation', {})
    risk = result_data.get('risk_assessment', {})
    
    cursor.execute('''
        INSERT INTO screenings (
            screening_id, timestamp, document_filename, selfie_filename, forensic_heatmap_filename,
            document_face_crop, selfie_face_crop, document_type, extracted_name, extracted_dob,
            extracted_doc_number, extracted_expiry, ocr_confidence, tampering_score,
            tampering_classification, face_similarity, face_match, composite_risk_score,
            risk_level, verdict, raw_ocr_json, tampering_details_json, face_details_json,
            validation_details_json, reasons_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        screening_id,
        timestamp,
        result_data.get('document_image'),
        result_data.get('selfie_image'),
        tampering.get('forensic_heatmap'),
        face.get('doc_face_crop'),
        face.get('selfie_face_crop'),
        ocr.get('document_type', 'Unknown'),
        ocr.get('extracted_fields', {}).get('name', {}).get('value', 'N/A'),
        ocr.get('extracted_fields', {}).get('dob', {}).get('value', 'N/A'),
        ocr.get('extracted_fields', {}).get('document_number', {}).get('value', 'N/A'),
        ocr.get('extracted_fields', {}).get('expiry_date', {}).get('value', 'N/A'),
        ocr.get('overall_confidence', 0.0),
        tampering.get('tampering_score', 0.0),
        tampering.get('classification', 'Normal'),
        face.get('similarity_score', 0.0),
        1 if face.get('is_match') else 0,
        risk.get('risk_score', 0.0),
        risk.get('risk_level', 'UNKNOWN'),
        risk.get('verdict', 'PENDING'),
        json.dumps(ocr),
        json.dumps(tampering),
        json.dumps(face),
        json.dumps(validation),
        json.dumps(risk.get('reasons', []))
    ))
    conn.commit()
    conn.close()
    return screening_id

def get_all_screenings(limit=100, offset=0, search=None, risk_filter=None, doc_type_filter=None):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM screenings WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (screening_id LIKE ? OR extracted_name LIKE ? OR extracted_doc_number LIKE ?)'
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])
    
    if risk_filter and risk_filter.upper() != 'ALL':
        query += ' AND risk_level = ?'
        params.append(risk_filter.upper())
        
    if doc_type_filter and doc_type_filter.upper() != 'ALL':
        query += ' AND document_type LIKE ?'
        params.append(f"%{doc_type_filter}%")
        
    query += ' ORDER BY id DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    screenings = [dict(row) for row in rows]
    conn.close()
    return screenings

def get_screening_by_id(screening_id):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM screenings WHERE screening_id = ?', (screening_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        data['ocr'] = json.loads(data['raw_ocr_json']) if data['raw_ocr_json'] else {}
        data['tampering'] = json.loads(data['tampering_details_json']) if data['tampering_details_json'] else {}
        data['face_verification'] = json.loads(data['face_details_json']) if data['face_details_json'] else {}
        data['validation'] = json.loads(data['validation_details_json']) if data['validation_details_json'] else {}
        data['reasons'] = json.loads(data['reasons_json']) if data['reasons_json'] else []
        return data
    return None

def delete_screening(screening_id):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM screenings WHERE screening_id = ?', (screening_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_screening_stats():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM screenings')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM screenings WHERE risk_level = ?', ('LOW',))
    low = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM screenings WHERE risk_level = ?', ('MEDIUM',))
    medium = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM screenings WHERE risk_level = ?', ('HIGH',))
    high = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(composite_risk_score) FROM screenings')
    avg_val = cursor.fetchone()[0]
    avg_score = avg_val if avg_val is not None else 0.0
    
    cursor.execute('SELECT COUNT(*) FROM screenings WHERE tampering_classification = ?', ('Suspicious',))
    tampered_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM screenings WHERE face_match = 1')
    face_matched_count = cursor.fetchone()[0]
    
    conn.close()
    return {
        'total': total,
        'low': low,
        'medium': medium,
        'high': high,
        'avg_risk_score': round(float(avg_score), 1),
        'tampered_count': tampered_count,
        'face_matched_count': face_matched_count
    }
