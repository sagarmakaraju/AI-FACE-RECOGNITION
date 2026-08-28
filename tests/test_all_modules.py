import unittest
import os
import json
import sqlite3
import numpy as np
import cv2

import config
import database
from modules.ocr_engine import OCREngine
from modules.tampering_detector import TamperingDetector
from modules.face_verifier import FaceVerifier
from modules.risk_engine import RiskEngine
from app import app
from scripts.generate_sample_data import create_sample_suite

class TestAllModules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_sample_suite()
        cls.ocr = OCREngine()
        cls.tampering = TamperingDetector()
        cls.face = FaceVerifier()
        cls.risk = RiskEngine()
        cls.app_client = app.test_client()

    def test_01_database(self):
        """Test SQLite database operations"""
        database.init_db()
        stats_before = database.get_screening_stats()
        self.assertIn("total", stats_before)
        
        dummy_data = {
            "screening_id": "TEST-SCR-001",
            "timestamp": "2026-08-27 12:00:00",
            "document_image": "doc_test.jpg",
            "selfie_image": "selfie_test.jpg",
            "ocr": {
                "document_type": "Aadhaar Card",
                "overall_confidence": 95.0,
                "extracted_fields": {
                    "name": {"value": "TEST USER"},
                    "dob": {"value": "01/01/1995"},
                    "document_number": {"value": "5489 2174 9633"},
                    "expiry_date": {"value": "Lifetime"}
                }
            },
            "tampering": {
                "tampering_score": 10.5,
                "classification": "Normal",
                "forensic_heatmap": "heat_test.jpg"
            },
            "face_verification": {
                "similarity_score": 88.0,
                "is_match": True,
                "doc_face_crop": "crop_doc.jpg",
                "selfie_face_crop": "crop_selfie.jpg"
            },
            "validation": {
                "doc_number_valid": True,
                "age_valid": True
            },
            "risk_assessment": {
                "risk_score": 12.0,
                "risk_level": "LOW",
                "verdict": "VERIFIED / APPROVED",
                "reasons": ["All checks passed successfully."]
            }
        }
        
        saved_id = database.save_screening(dummy_data)
        self.assertEqual(saved_id, "TEST-SCR-001")
        
        record = database.get_screening_by_id("TEST-SCR-001")
        self.assertIsNotNone(record)
        self.assertEqual(record["document_type"], "Aadhaar Card")
        self.assertEqual(record["extracted_name"], "TEST USER")
        self.assertEqual(record["risk_level"], "LOW")
        
        screenings = database.get_all_screenings(search="TEST USER")
        self.assertTrue(len(screenings) >= 1)
        
        deleted = database.delete_screening("TEST-SCR-001")
        self.assertTrue(deleted)
        self.assertIsNone(database.get_screening_by_id("TEST-SCR-001"))

    def test_02_ocr_engine(self):
        """Test OCR text and entity extraction on clean Aadhaar"""
        img_path = "static/samples/sample_clean_aadhaar.jpg"
        self.assertTrue(os.path.exists(img_path))
        
        res = self.ocr.process(img_path)
        self.assertIn("document_type", res)
        self.assertEqual(res["document_type"], "Aadhaar Card")
        self.assertTrue(res["overall_confidence"] > 50.0)
        self.assertEqual(res["extracted_fields"]["document_number"]["value"], "5489 2174 9633")
        self.assertEqual(res["extracted_fields"]["dob"]["value"], "14/11/1992")

    def test_03_tampering_detector(self):
        """Test ELA and tampering analysis on clean vs tampered images"""
        clean_path = "static/samples/sample_clean_aadhaar.jpg"
        tampered_path = "static/samples/sample_tampered_pan.jpg"
        
        res_clean = self.tampering.analyze(clean_path)
        res_tampered = self.tampering.analyze(tampered_path)
        
        self.assertIn("tampering_score", res_clean)
        self.assertIn("classification", res_clean)
        self.assertIn("forensic_heatmap", res_clean)
        self.assertTrue(res_tampered["tampering_score"] >= 25.0)

    def test_04_face_verifier(self):
        """Test face matching and mismatching"""
        doc_path = "static/samples/sample_clean_aadhaar.jpg"
        match_selfie = "static/samples/selfie_person1.jpg"
        mismatch_selfie = "static/samples/selfie_mismatch.jpg"
        
        res_match = self.face.verify(doc_path, match_selfie)
        self.assertIn("similarity_score", res_match)
        self.assertTrue(res_match["is_match"])
        
        res_mismatch = self.face.verify(doc_path, mismatch_selfie)
        self.assertIn("is_match", res_mismatch)

    def test_05_risk_engine(self):
        """Test checksums, validation, and composite risk scoring"""
        self.assertTrue(self.risk.validate_verhoeff_aadhaar("5489 2174 9633"))
        self.assertFalse(self.risk.validate_verhoeff_aadhaar("1234 5678 9012"))
        
        is_pan_valid, msg = self.risk.validate_pan_format("ABCPE1234F")
        self.assertTrue(is_pan_valid)
        self.assertIn("Individual Person", msg)
        
        is_invalid_pan, _ = self.risk.validate_pan_format("12345ABCDE")
        self.assertFalse(is_invalid_pan)

    def test_06_flask_api(self):
        """Test Flask HTTP and REST API endpoints"""
        res_home = self.app_client.get('/')
        self.assertEqual(res_home.status_code, 200)
        
        res_hist = self.app_client.get('/history')
        self.assertEqual(res_hist.status_code, 200)
        
        res_stats = self.app_client.get('/api/stats')
        self.assertEqual(res_stats.status_code, 200)
        data_stats = json.loads(res_stats.data)
        self.assertIn("total", data_stats)
        
        res_samples = self.app_client.get('/api/samples')
        self.assertEqual(res_samples.status_code, 200)
        samples_list = json.loads(res_samples.data)
        self.assertEqual(len(samples_list), 4)
        
        res_verify = self.app_client.post('/api/verify', data={"sample_id": "clean_aadhaar"})
        self.assertEqual(res_verify.status_code, 200)
        verify_data = json.loads(res_verify.data)
        self.assertEqual(verify_data["status"], "success")
        self.assertIn("screening_id", verify_data)
        self.assertIn("risk_assessment", verify_data)

if __name__ == '__main__':
    unittest.main()
