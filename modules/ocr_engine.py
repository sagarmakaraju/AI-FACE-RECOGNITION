import re
import cv2
import numpy as np
from rapidocr_onnxruntime import RapidOCR
import os

class OCREngine:
    def __init__(self):
        self.ocr = RapidOCR()

    def preprocess_image(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image at {image_path}")
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        return img, gray, enhanced

    def extract_text(self, image_path):
        img, gray, enhanced = self.preprocess_image(image_path)
        result, _ = self.ocr(img)
        
        if not result or len(result) == 0:
            result, _ = self.ocr(enhanced)
            
        detections = []
        if result:
            for item in result:
                bbox = item[0]
                text = str(item[1]).strip()
                score = float(item[2])
                if text:
                    detections.append({
                        "text": text,
                        "confidence": round(score * 100, 2),
                        "bbox": bbox
                    })
        return img, detections

    def classify_document(self, text_corpus):
        text_upper = text_corpus.upper()
        if re.search(r"AADHAAR|UNIQUE IDENTIFICATION|UIDAI|GOVERNMENT OF INDIA|MERA AADHAAR|\b\d{4}\s\d{4}\s\d{4}\b", text_upper):
            return "Aadhaar Card"
        elif re.search(r"INCOME TAX|PERMANENT ACCOUNT|PAN CARD|[A-Z]{5}[0-9]{4}[A-Z]", text_upper):
            return "PAN Card"
        elif re.search(r"PASSPORT|REPUBLIC OF INDIA|P<IND|[A-Z][0-9]{7}", text_upper):
            return "Passport"
        elif re.search(r"DRIVING LICEN[CS]E|UNION OF INDIA|TRANSPORT DEPARTMENT|DL NO", text_upper):
            return "Driving License"
        elif re.search(r"ELECTION COMMISSION|VOTER|EPIC NO|ELECTORAL", text_upper):
            return "Voter ID"
        return "Generic Government ID"

    def extract_dob(self, text_lines, raw_text):
        dob_patterns = [
            r"(?:DOB|D\.O\.B|Date of Birth|Birth Date|Birth)\s*[:\-\s]?\s*([0-3]?[0-9][/\-.][0-1]?[0-9][/\-.](?:19|20)\d{2})",
            r"\b([0-3]?[0-9][/\-.][0-1]?[0-9][/\-.](?:19|20)\d{2})\b",
            r"([0-3]?[0-9]\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2})",
            r"(?:Year of Birth|YOB)\s*[:\-\s]?\s*((?:19|20)\d{2})"
        ]
        
        for pattern in dob_patterns:
            for line_item in text_lines:
                text = line_item["text"]
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = match.group(1).replace(".", "/").replace("-", "/")
                    return val, line_item["confidence"]
                    
        for pattern in dob_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                val = match.group(1).replace(".", "/").replace("-", "/")
                return val, 75.0
                
        return "N/A", 0.0

    def extract_expiry(self, text_lines, raw_text, doc_type):
        if doc_type in ["Aadhaar Card", "PAN Card"]:
            return "Lifetime / Not Applicable", 95.0
            
        expiry_patterns = [
            r"(?:Expiry|Valid Till|Validity|Valid Upto|Exp\.?\s*Date|Expires)\s*[:\-\s]?\s*([0-3]?[0-9][/\-.][0-1]?[0-9][/\-.](?:20)\d{2})",
            r"(?:Valid To|Expiry Date)\s*[:\-\s]?\s*([0-3]?[0-9][/\-.][0-1]?[0-9][/\-.](?:20)\d{2})"
        ]
        
        for pattern in expiry_patterns:
            for line_item in text_lines:
                text = line_item["text"]
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = match.group(1).replace(".", "/").replace("-", "/")
                    return val, line_item["confidence"]
                    
        for pattern in expiry_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                val = match.group(1).replace(".", "/").replace("-", "/")
                return val, 70.0
                
        return "N/A", 0.0

    def extract_document_number(self, text_lines, raw_text, doc_type):
        aadhaar_pattern = r"\b([2-9]\d{3}\s?\d{4}\s?\d{4})\b"
        pan_pattern = r"\b([A-Z]{5}[0-9]{4}[A-Z])\b"
        passport_pattern = r"(?:Passport\s*No|Passport\s*Number|Doc\s*No)?\s*[:\-\s]?\s*\b([A-PR-WYa-pr-wy][0-9]{7,8})\b"
        dl_pattern = r"(?:DL\s*No|Licence\s*No)?\s*[:\-\s]?\s*\b([A-Z]{2}[0-9\-\s]{12,17})\b"
        voter_pattern = r"\b([A-Z]{3}[0-9]{7})\b"
        
        for line_item in text_lines:
            text = line_item["text"].strip().upper()
            if doc_type == "Aadhaar Card":
                m = re.search(aadhaar_pattern, text)
                if m:
                    raw_digits = m.group(1).replace(" ", "")
                    return f"{raw_digits[:4]} {raw_digits[4:8]} {raw_digits[8:]}", line_item["confidence"]
            elif doc_type == "PAN Card":
                m = re.search(pan_pattern, text)
                if m:
                    return m.group(1), line_item["confidence"]
            elif doc_type == "Passport":
                m = re.search(passport_pattern, text)
                if m:
                    return m.group(1), line_item["confidence"]
            elif doc_type == "Driving License":
                m = re.search(dl_pattern, text)
                if m:
                    return m.group(1), line_item["confidence"]
            elif doc_type == "Voter ID":
                m = re.search(voter_pattern, text)
                if m:
                    return m.group(1), line_item["confidence"]
                    
        # Corpus search
        if doc_type == "Aadhaar Card":
            m = re.search(aadhaar_pattern, raw_text)
            if m:
                raw_digits = m.group(1).replace(" ", "")
                return f"{raw_digits[:4]} {raw_digits[4:8]} {raw_digits[8:]}", 85.0
        elif doc_type == "PAN Card":
            m = re.search(pan_pattern, raw_text.upper())
            if m:
                return m.group(1), 85.0
        elif doc_type == "Passport":
            m = re.search(passport_pattern, raw_text, re.IGNORECASE)
            if m:
                return m.group(1).upper(), 85.0
        elif doc_type == "Driving License":
            m = re.search(dl_pattern, raw_text, re.IGNORECASE)
            if m:
                return m.group(1).upper(), 85.0
                
        return "N/A", 0.0

    def extract_name(self, text_lines, doc_type):
        ignore_keywords = [
            "GOVERNMENT", "INDIA", "INCOME", "TAX", "DEPARTMENT", "PERMANENT",
            "ACCOUNT", "NUMBER", "CARD", "AADHAAR", "UIDAI", "MERA", "FATHER",
            "SIGNATURE", "DATE", "BIRTH", "DOB", "MALE", "FEMALE", "GENDER",
            "REPUBLIC", "PASSPORT", "UNION", "DRIVING", "LICENCE", "TRANSPORT",
            "AUTHORITY", "ELECTOR", "COMMISSION", "PHOTO", "ENROLLMENT", "HELP",
            "GIVEN", "SURNAME"
        ]
        
        for line_item in text_lines:
            text = line_item["text"].strip()
            # Handle Given Name / Surname on Passports
            given_match = re.search(r"(?:Given Name|Given Names)\s*[:\-\s]?\s*([A-Za-z\s\.]{2,30})", text, re.IGNORECASE)
            if given_match:
                return given_match.group(1).strip().title(), line_item["confidence"]
            name_match = re.search(r"(?:Name|Full Name|Holder)\s*[:\-\s]?\s*([A-Za-z\s\.]{3,40})", text, re.IGNORECASE)
            if name_match:
                cand = name_match.group(1).strip()
                if not any(k in cand.upper() for k in ignore_keywords):
                    return cand.title(), line_item["confidence"]
                    
        # Sequential line inspection
        if doc_type == "PAN Card":
            for line_item in text_lines:
                text = line_item["text"].strip()
                words = text.split()
                if 1 <= len(words) <= 4 and re.match(r"^[A-Za-z\s\.]+$", text):
                    if not any(k in text.upper() for k in ignore_keywords) and len(text) > 3:
                        return text.title(), line_item["confidence"]
                        
        if doc_type == "Aadhaar Card":
            for i, line_item in enumerate(text_lines):
                text = line_item["text"].strip()
                if re.search(r"DOB|Year of Birth|Birth|Gender|Male|Female", text, re.IGNORECASE) and i > 0:
                    prev_text = text_lines[i-1]["text"].strip()
                    if re.match(r"^[A-Za-z\s\.]+$", prev_text) and not any(k in prev_text.upper() for k in ignore_keywords):
                        return prev_text.title(), text_lines[i-1]["confidence"]
                        
        for line_item in text_lines:
            text = line_item["text"].strip()
            words = text.split()
            if 2 <= len(words) <= 4 and re.match(r"^[A-Za-z\s\.]+$", text):
                if not any(k in text.upper() for k in ignore_keywords) and len(text) > 4:
                    return text.title(), line_item["confidence"]
                    
        return "N/A", 0.0

    def extract_gender(self, text_lines, raw_text):
        for line_item in text_lines:
            text = line_item["text"].upper()
            if "FEMALE" in text:
                return "Female", line_item["confidence"]
            elif "MALE" in text:
                return "Male", line_item["confidence"]
            elif "TRANSGENDER" in text:
                return "Transgender", line_item["confidence"]
                
        if re.search(r"\bFEMALE\b", raw_text, re.IGNORECASE):
            return "Female", 80.0
        elif re.search(r"\bMALE\b", raw_text, re.IGNORECASE):
            return "Male", 80.0
            
        return "N/A", 0.0

    def annotate_image(self, img, text_lines, output_path):
        annotated = img.copy()
        for item in text_lines:
            bbox = item.get("bbox")
            if bbox is not None and len(bbox) == 4:
                pts = np.array(bbox, np.int32).reshape((-1, 1, 2))
                cv2.polylines(annotated, [pts], isClosed=True, color=(0, 220, 0), thickness=2)
        cv2.imwrite(output_path, annotated)
        return output_path

    def process(self, image_path, annotated_output_path=None):
        img, detections = self.extract_text(image_path)
        all_texts = [d["text"] for d in detections]
        raw_text = " \n ".join(all_texts)
        
        confidences = [d["confidence"] for d in detections]
        overall_confidence = round(sum(confidences) / len(confidences), 1) if confidences else 0.0
        
        doc_type = self.classify_document(raw_text)
        name, name_conf = self.extract_name(detections, doc_type)
        dob, dob_conf = self.extract_dob(detections, raw_text)
        doc_number, num_conf = self.extract_document_number(detections, raw_text, doc_type)
        expiry, exp_conf = self.extract_expiry(detections, raw_text, doc_type)
        gender, gen_conf = self.extract_gender(detections, raw_text)
        
        annotated_file = None
        if annotated_output_path:
            self.annotate_image(img, detections, annotated_output_path)
            annotated_file = os.path.basename(annotated_output_path)
            
        return {
            "document_type": doc_type,
            "overall_confidence": overall_confidence,
            "annotated_image": annotated_file,
            "full_text": raw_text,
            "extracted_fields": {
                "name": {"value": name, "confidence": name_conf},
                "dob": {"value": dob, "confidence": dob_conf},
                "document_number": {"value": doc_number, "confidence": num_conf},
                "expiry_date": {"value": expiry, "confidence": exp_conf},
                "gender": {"value": gender, "confidence": gen_conf}
            },
            "detections_count": len(detections),
            "detections": detections
        }
