import re
import datetime

# Standard Verhoeff algorithm tables
VERHOEFF_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]

VERHOEFF_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]

VERHOEFF_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

class RiskEngine:
    def __init__(self):
        pass

    def validate_verhoeff_aadhaar(self, aadhaar_str):
        """
        Validates 12-digit Aadhaar number using Verhoeff checksum algorithm
        """
        clean_num = aadhaar_str.replace(" ", "").replace("-", "").strip()
        if len(clean_num) != 12 or not clean_num.isdigit():
            return False
            
        c = 0
        num = [int(x) for x in reversed(clean_num)]
        for i, item in enumerate(num):
            c = VERHOEFF_D[c][VERHOEFF_P[i % 8][item]]
        return c == 0

    def validate_pan_format(self, pan_str):
        clean_pan = pan_str.replace(" ", "").strip().upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", clean_pan):
            return False, "Invalid PAN syntax (expected 5 letters, 4 numbers, 1 letter)"
            
        entity_char = clean_pan[3]
        valid_entities = {
            'P': 'Individual Person',
            'C': 'Company',
            'H': 'Hindu Undivided Family',
            'F': 'Firm / Partnership',
            'A': 'Association of Persons',
            'T': 'Trust',
            'B': 'Body of Individuals',
            'L': 'Local Authority',
            'J': 'Artificial Juridical Person',
            'G': 'Government Agency'
        }
        if entity_char not in valid_entities:
            return False, f"Unknown PAN entity code: {entity_char}"
            
        return True, f"Valid PAN format ({valid_entities[entity_char]})"

    def parse_date(self, date_str):
        if not date_str or date_str.upper() in ["N/A", "LIFETIME / NOT APPLICABLE", "LIFETIME"]:
            return None
        formats = ["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y", "%d %b %Y", "%d %B %Y", "%Y/%m/%d"]
        clean = re.sub(r"[^\d/A-Za-z\s\.-]", "", date_str).strip()
        for fmt in formats:
            try:
                return datetime.datetime.strptime(clean, fmt).date()
            except Exception:
                pass
        return None

    def validate_document(self, ocr_data):
        doc_type = ocr_data.get("document_type", "Unknown")
        fields = ocr_data.get("extracted_fields", {})
        
        name_val = fields.get("name", {}).get("value", "N/A")
        dob_val = fields.get("dob", {}).get("value", "N/A")
        doc_num_val = fields.get("document_number", {}).get("value", "N/A")
        expiry_val = fields.get("expiry_date", {}).get("value", "N/A")
        
        validation_results = {
            "name_valid": name_val != "N/A" and len(name_val) > 2,
            "dob_valid": False,
            "age_valid": False,
            "age_years": None,
            "doc_number_valid": False,
            "expiry_valid": True,
            "is_expired": False,
            "doc_number_notes": "",
            "validation_failures": []
        }
        
        # Name Check
        if not validation_results["name_valid"]:
            validation_results["validation_failures"].append("Applicant Name could not be verified from OCR")
            
        # DOB Check
        dob_date = self.parse_date(dob_val)
        if dob_date:
            validation_results["dob_valid"] = True
            today = datetime.date.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            validation_results["age_years"] = age
            
            if dob_date > today:
                validation_results["validation_failures"].append("DOB is in the future")
            elif age < 18:
                validation_results["validation_failures"].append(f"Applicant is a minor (Age: {age} < 18)")
            elif age > 115:
                validation_results["validation_failures"].append(f"Unreasonable age ({age} years)")
            else:
                validation_results["age_valid"] = True
        else:
            if dob_val != "N/A":
                validation_results["dob_valid"] = True
                validation_results["age_valid"] = True
            else:
                validation_results["validation_failures"].append("Date of Birth not detected")
                
        # Doc Number Validation
        if doc_type == "Aadhaar Card":
            clean_aadhaar = doc_num_val.replace(" ", "")
            if len(clean_aadhaar) == 12 and clean_aadhaar.isdigit():
                is_verhoeff_ok = self.validate_verhoeff_aadhaar(clean_aadhaar)
                validation_results["doc_number_valid"] = True
                validation_results["doc_number_notes"] = "Valid 12-digit Aadhaar" + (" (Verhoeff verified)" if is_verhoeff_ok else "")
            else:
                validation_results["validation_failures"].append("Invalid Aadhaar number (expected 12 digits)")
        elif doc_type == "PAN Card":
            is_pan_ok, pan_msg = self.validate_pan_format(doc_num_val)
            validation_results["doc_number_valid"] = is_pan_ok
            validation_results["doc_number_notes"] = pan_msg
            if not is_pan_ok:
                validation_results["validation_failures"].append(f"Invalid PAN format: {pan_msg}")
        elif doc_type == "Passport":
            if re.match(r"^[A-PR-WYa-pr-wy][0-9]{7,8}$", doc_num_val.replace(" ", "")):
                validation_results["doc_number_valid"] = True
                validation_results["doc_number_notes"] = "Valid Passport standard"
            else:
                validation_results["validation_failures"].append("Invalid Passport format")
        else:
            if doc_num_val != "N/A" and len(doc_num_val) > 4:
                validation_results["doc_number_valid"] = True
                validation_results["doc_number_notes"] = "Document number detected"
            else:
                validation_results["validation_failures"].append("Document identifier number missing")
                
        # Expiry Check
        if doc_type not in ["Aadhaar Card", "PAN Card"] and expiry_val not in ["N/A", "Lifetime / Not Applicable"]:
            exp_date = self.parse_date(expiry_val)
            if exp_date:
                today = datetime.date.today()
                if exp_date < today:
                    validation_results["is_expired"] = True
                    validation_results["expiry_valid"] = False
                    validation_results["validation_failures"].append(f"Document expired on {exp_date.strftime('%d/%m/%Y')}")
                else:
                    validation_results["expiry_valid"] = True
                    
        return validation_results

    def assess_risk(self, ocr_data, tampering_data, face_data, validation_data):
        reasons = []
        
        # 1. OCR Risk
        ocr_conf = ocr_data.get("overall_confidence", 0.0)
        ocr_risk = 0.0
        if ocr_conf < 50.0:
            ocr_risk += 45.0
            reasons.append(f"Low overall OCR extraction confidence ({ocr_conf}%)")
        elif ocr_conf < 70.0:
            ocr_risk += 20.0
            
        fields = ocr_data.get("extracted_fields", {})
        if fields.get("name", {}).get("value") == "N/A":
            ocr_risk += 30.0
        if fields.get("document_number", {}).get("value") == "N/A":
            ocr_risk += 30.0
        if fields.get("dob", {}).get("value") == "N/A":
            ocr_risk += 15.0
        ocr_risk = min(ocr_risk, 100.0)
        
        # 2. Validation Risk
        val_risk = 0.0
        failures = validation_data.get("validation_failures", [])
        if not validation_data.get("doc_number_valid"):
            val_risk += 50.0
        if validation_data.get("is_expired"):
            val_risk += 45.0
        if not validation_data.get("name_valid"):
            val_risk += 25.0
        if not validation_data.get("dob_valid"):
            val_risk += 15.0
        val_risk = min(val_risk + (len(failures) * 15.0), 100.0)
        
        for fail in failures:
            reasons.append(f"Validation Failure: {fail}")
            
        # 3. Tampering Risk
        tampering_score = tampering_data.get("tampering_score", 0.0)
        tamper_risk = tampering_score
        
        if tampering_score >= 55.0:
            reasons.append(f"High Tampering Probability ({tampering_score}/100) detected by ELA/Noise forensics")
            for ind in tampering_data.get("suspicious_indicators", []):
                reasons.append(f"Forensic Flag: {ind}")
        elif tampering_score >= 25.0:
            reasons.append(f"Minor image compression inconsistency ({tampering_score}/100)")
            
        # 4. Face Verification Risk
        face_sim = face_data.get("similarity_score", 0.0)
        is_face_match = face_data.get("is_match", False)
        
        if not face_data.get("doc_face_detected") or not face_data.get("selfie_face_detected"):
            face_risk = 100.0
            reasons.append(f"Biometric Failure: {face_data.get('message', 'Face not detected')}")
        elif not is_face_match:
            face_risk = max(100.0 - face_sim, 65.0)
            reasons.append(f"Face Biometric Mismatch: Similarity only {face_sim}%")
        else:
            face_risk = max(0.0, (100.0 - face_sim) * 0.4)
            reasons.append(f"Face Biometric Match: {face_sim}% similarity verified")
            
        # Composite Weighted Score
        composite_score = (0.20 * ocr_risk) + (0.20 * val_risk) + (0.30 * tamper_risk) + (0.30 * face_risk)
        composite_score = round(float(min(max(composite_score, 0.0), 100.0)), 1)
        
        if composite_score <= 25.0:
            risk_level = "LOW"
            verdict = "VERIFIED / APPROVED"
        elif composite_score <= 55.0:
            risk_level = "MEDIUM"
            verdict = "MANUAL REVIEW REQUIRED"
        else:
            risk_level = "HIGH"
            verdict = "REJECTED / SUSPECT FRAUD"
            
        if risk_level == "LOW":
            reasons.insert(0, "All primary identity verification, tamper forensics, and facial biometric checks PASSED.")
        elif risk_level == "MEDIUM":
            reasons.insert(0, "Document flagged for manual review due to moderate inconsistencies or low OCR confidence.")
        else:
            reasons.insert(0, "CRITICAL RISK: Identity document rejected due to tampering artifacts or biometric mismatch.")
            
        return {
            "risk_score": composite_score,
            "risk_level": risk_level,
            "verdict": verdict,
            "sub_scores": {
                "ocr_risk": round(ocr_risk, 1),
                "validation_risk": round(val_risk, 1),
                "tampering_risk": round(tamper_risk, 1),
                "face_risk": round(face_risk, 1)
            },
            "reasons": reasons
        }
