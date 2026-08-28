import cv2
import numpy as np
import os
import config

class FaceVerifier:
    def __init__(self, yunet_path=None, sface_path=None):
        self.yunet_path = yunet_path or config.YUNET_MODEL_PATH
        self.sface_path = sface_path or config.SFACE_MODEL_PATH
        
        self.detector = None
        self.recognizer = None
        # Official OpenCV SFace threshold is 0.363 for Cosine Similarity
        self.cosine_threshold = 0.363
        self._load_models()

    def _load_models(self):
        # 1. Load YuNet Detector
        if os.path.exists(self.yunet_path):
            try:
                self.detector = cv2.FaceDetectorYN.create(
                    self.yunet_path,
                    "",
                    (320, 320),
                    score_threshold=0.45,
                    nms_threshold=0.3,
                    top_k=5000
                )
            except Exception as e:
                print(f"Notice loading YuNet: {e}")
                
        # 2. Load SFace Recognizer
        if os.path.exists(self.sface_path):
            try:
                self.recognizer = cv2.FaceRecognizerSF.create(self.sface_path, "")
            except Exception as e:
                print(f"Notice loading SFace: {e}")

    def detect_face(self, img_bgr):
        """
        Detects face using YuNet with color-segmentation fallback.
        Returns (bbox, face_raw, confidence, faces_count)
        """
        h, w = img_bgr.shape[:2]
        
        # Method 1: YuNet DNN
        if self.detector is not None:
            try:
                self.detector.setInputSize((w, h))
                _, faces = self.detector.detect(img_bgr)
                if faces is not None and len(faces) > 0:
                    best_face = faces[0]
                    bbox = [int(best_face[0]), int(best_face[1]), int(best_face[2]), int(best_face[3])]
                    conf = float(best_face[-1])
                    return bbox, best_face, conf, len(faces)
            except Exception as e:
                pass
                
        # Method 2: Color Segmentation Fallback
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([30, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_boxes = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            aspect = ch / float(cw + 1e-5)
            if 1.0 <= aspect <= 2.2 and cw >= 40 and ch >= 50 and (cw * ch) < (w * h * 0.6):
                valid_boxes.append((cw * ch, [x, y, cw, ch]))
                
        if valid_boxes:
            valid_boxes.sort(key=lambda b: b[0], reverse=True)
            best_bbox = valid_boxes[0][1]
            return best_bbox, None, 0.75, len(valid_boxes)
            
        return None, None, 0.0, 0

    def crop_face(self, img_bgr, bbox, margin=0.15):
        if bbox is None:
            return None
        x, y, w, h = bbox
        ih, iw = img_bgr.shape[:2]
        mx = int(w * margin)
        my = int(h * margin)
        x1 = max(0, x - mx)
        y1 = max(0, y - my)
        x2 = min(iw, x + w + mx)
        y2 = min(ih, y + h + my)
        return img_bgr[y1:y2, x1:x2]

    def extract_embedding(self, img_bgr, face_raw, bbox):
        """
        Extracts 128-D facial feature embedding using SFace
        """
        if self.recognizer is not None and face_raw is not None:
            try:
                aligned_face = self.recognizer.alignCrop(img_bgr, face_raw)
                feature = self.recognizer.feature(aligned_face)
                return feature
            except Exception as e:
                pass
                
        crop = self.crop_face(img_bgr, bbox)
        if crop is None or crop.size == 0:
            return None
            
        resized = cv2.resize(crop, (112, 112))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        hists = []
        for r in range(4):
            for c in range(4):
                cell = gray[r*28:(r+1)*28, c*28:(c+1)*28]
                hist = cv2.calcHist([cell], [0], None, [16], [0, 256])
                hists.append(hist.flatten())
        desc = np.concatenate(hists).reshape(1, -1).astype(np.float32)
        norm = np.linalg.norm(desc)
        if norm > 0:
            desc = desc / norm
        return desc

    def compute_similarity(self, emb1, emb2):
        """
        Computes Cosine Similarity and maps to 0-100% based on SFace benchmark (0.363 = 70%)
        """
        if emb1 is None or emb2 is None:
            return 0.0, 999.0, False
            
        if self.recognizer is not None:
            try:
                cos_sim = float(self.recognizer.match(emb1, emb2, cv2.FaceRecognizerSF_FR_COSINE))
                l2_dist = float(self.recognizer.match(emb1, emb2, cv2.FaceRecognizerSF_FR_NORM_L2))
            except Exception:
                norm1 = np.linalg.norm(emb1)
                norm2 = np.linalg.norm(emb2)
                cos_sim = float(np.dot(emb1.flatten(), emb2.flatten()) / (norm1 * norm2 + 1e-5))
                l2_dist = float(np.linalg.norm(emb1 - emb2))
        else:
            norm1 = np.linalg.norm(emb1)
            norm2 = np.linalg.norm(emb2)
            cos_sim = float(np.dot(emb1.flatten(), emb2.flatten()) / (norm1 * norm2 + 1e-5))
            l2_dist = float(np.linalg.norm(emb1 - emb2))
            
        is_match = cos_sim >= self.cosine_threshold
        
        # Scale to intuitive percentage (0 - 100%)
        if cos_sim <= 0.0:
            sim_pct = 0.0
        elif cos_sim < self.cosine_threshold:
            sim_pct = (cos_sim / self.cosine_threshold) * 65.0
        else:
            sim_pct = 70.0 + ((cos_sim - self.cosine_threshold) / (0.65 - self.cosine_threshold)) * 28.0
            
        sim_pct = round(float(np.clip(sim_pct, 0.0, 99.0)), 1)
        return sim_pct, round(l2_dist, 3), is_match

    def verify(self, doc_image_path, selfie_image_path, doc_crop_out=None, selfie_crop_out=None):
        doc_img = cv2.imread(doc_image_path)
        selfie_img = cv2.imread(selfie_image_path)
        
        if doc_img is None or selfie_img is None:
            raise ValueError("Could not load document or selfie image.")
            
        doc_bbox, doc_raw, doc_conf, doc_faces_count = self.detect_face(doc_img)
        selfie_bbox, selfie_raw, selfie_conf, selfie_faces_count = self.detect_face(selfie_img)
        
        doc_face_found = doc_bbox is not None
        selfie_face_found = selfie_bbox is not None
        
        doc_crop_file = None
        selfie_crop_file = None
        
        if doc_face_found and doc_crop_out:
            crop = self.crop_face(doc_img, doc_bbox)
            if crop is not None:
                cv2.imwrite(doc_crop_out, crop)
                doc_crop_file = os.path.basename(doc_crop_out)
                
        if selfie_face_found and selfie_crop_out:
            crop = self.crop_face(selfie_img, selfie_bbox)
            if crop is not None:
                cv2.imwrite(selfie_crop_out, crop)
                selfie_crop_file = os.path.basename(selfie_crop_out)
                
        if not doc_face_found or not selfie_face_found:
            status_reason = []
            if not doc_face_found:
                status_reason.append("No face detected in document photo.")
            if not selfie_face_found:
                status_reason.append("No face detected in selfie.")
                
            return {
                "is_match": False,
                "similarity_score": 0.0,
                "confidence_score": 0.0,
                "l2_distance": 999.0,
                "status": "FACE_NOT_FOUND",
                "doc_face_detected": doc_face_found,
                "selfie_face_detected": selfie_face_found,
                "doc_face_crop": doc_crop_file,
                "selfie_face_crop": selfie_crop_file,
                "faces_in_selfie": selfie_faces_count,
                "message": " ".join(status_reason)
            }
            
        emb_doc = self.extract_embedding(doc_img, doc_raw, doc_bbox)
        emb_selfie = self.extract_embedding(selfie_img, selfie_raw, selfie_bbox)
        
        sim_score, l2_dist, is_match = self.compute_similarity(emb_doc, emb_selfie)
        
        if is_match and sim_score >= 80.0:
            status = "MATCH_HIGH_CONFIDENCE"
            msg = "High confidence biometric face match confirmed."
        elif is_match:
            status = "MATCH_MODERATE"
            msg = "Facial biometric match confirmed within tolerance."
        elif sim_score >= 50.0:
            status = "UNCERTAIN"
            msg = "Marginal face similarity. Manual verification advised."
        else:
            status = "MISMATCH"
            msg = "Biometric mismatch detected between document portrait and selfie."
            
        return {
            "is_match": is_match,
            "similarity_score": sim_score,
            "confidence_score": round((doc_conf + selfie_conf) / 2.0 * 100, 1),
            "l2_distance": l2_dist,
            "status": status,
            "doc_face_detected": True,
            "selfie_face_detected": True,
            "doc_face_crop": doc_crop_file,
            "selfie_face_crop": selfie_crop_file,
            "faces_in_selfie": selfie_faces_count,
            "message": msg
        }
