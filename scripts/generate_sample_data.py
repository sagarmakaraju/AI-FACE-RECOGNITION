import cv2
import numpy as np
import os
import random

def draw_synthetic_face(seed=42, gender="male", skin_tone=(210, 185, 160), hair_color=(30, 25, 25)):
    random.seed(seed)
    np.random.seed(seed)
    
    img = np.ones((300, 260, 3), dtype=np.uint8) * 235
    for y in range(300):
        img[y, :, 0] = int(210 + (y / 300.0) * 30)
        img[y, :, 1] = int(220 + (y / 300.0) * 20)
        img[y, :, 2] = int(230 + (y / 300.0) * 15)
        
    shirt_color = (random.randint(40, 90), random.randint(50, 100), random.randint(110, 170)) if gender == "male" else (random.randint(120, 180), random.randint(60, 100), random.randint(140, 200))
    cv2.ellipse(img, (130, 320), (120, 90), 0, 0, 360, shirt_color, -1)
    
    neck_color = (int(skin_tone[0]*0.88), int(skin_tone[1]*0.88), int(skin_tone[2]*0.88))
    cv2.rectangle(img, (110, 170), (150, 230), neck_color, -1)
    
    face_w = 65 if gender == "male" else 55
    cv2.ellipse(img, (130, 140), (face_w, 78), 0, 0, 360, skin_tone, -1)
    
    if gender == "male":
        cv2.ellipse(img, (130, 95), (70, 50), 0, 180, 360, hair_color, -1)
        cv2.circle(img, (70, 120), 16, hair_color, -1)
        cv2.circle(img, (190, 120), 16, hair_color, -1)
    else:
        cv2.ellipse(img, (130, 90), (75, 55), 0, 180, 360, hair_color, -1)
        cv2.rectangle(img, (60, 90), (85, 260), hair_color, -1)
        cv2.rectangle(img, (175, 90), (200, 260), hair_color, -1)
    
    cv2.line(img, (90, 115), (120, 115), hair_color, 4)
    cv2.line(img, (140, 115), (170, 115), hair_color, 4)
    
    cv2.ellipse(img, (105, 128), (12, 7), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (105, 128), 5, (40, 30, 25), -1)
    cv2.circle(img, (107, 126), 2, (255, 255, 255), -1)
    
    cv2.ellipse(img, (155, 128), (12, 7), 0, 0, 360, (255, 255, 255), -1)
    cv2.circle(img, (155, 128), 5, (40, 30, 25), -1)
    cv2.circle(img, (157, 126), 2, (255, 255, 255), -1)
    
    cv2.line(img, (130, 128), (126, 158), (int(skin_tone[0]*0.75), int(skin_tone[1]*0.75), int(skin_tone[2]*0.75)), 2)
    cv2.line(img, (126, 158), (136, 158), (int(skin_tone[0]*0.75), int(skin_tone[1]*0.75), int(skin_tone[2]*0.75)), 2)
    
    cv2.ellipse(img, (130, 182), (18, 7), 0, 0, 180, (90, 70, 180), -1)
    return img

def create_sample_suite():
    os.makedirs("static/samples", exist_ok=True)
    
    # 1. Clean Aadhaar & Matching Selfie
    face1_doc = draw_synthetic_face(seed=101, gender="male", skin_tone=(210, 185, 160), hair_color=(30, 25, 25))
    face1_selfie = draw_synthetic_face(seed=101, gender="male", skin_tone=(210, 185, 160), hair_color=(30, 25, 25))
    cv2.imwrite("static/samples/selfie_person1.jpg", face1_selfie)
    
    aadhaar_img = np.ones((480, 750, 3), dtype=np.uint8) * 255
    aadhaar_img[0:15, :, :] = (40, 110, 240)
    aadhaar_img[15:25, :, :] = (255, 255, 255)
    aadhaar_img[25:35, :, :] = (60, 160, 40)
    cv2.rectangle(aadhaar_img, (5, 5), (745, 475), (200, 200, 200), 2)
    
    face_resized = cv2.resize(face1_doc, (140, 170))
    aadhaar_img[120:290, 50:190] = face_resized
    cv2.rectangle(aadhaar_img, (50, 120), (190, 290), (160, 160, 160), 2)
    
    cv2.putText(aadhaar_img, "GOVERNMENT OF INDIA", (220, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (120, 50, 20), 2)
    cv2.putText(aadhaar_img, "Unique Identification Authority of India", (220, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (80, 80, 80), 1)
    cv2.putText(aadhaar_img, "Name: ARUN KUMAR VERMA", (220, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    cv2.putText(aadhaar_img, "DOB: 14/11/1992", (220, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(aadhaar_img, "Gender: Male", (220, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(aadhaar_img, "5489 2174 9633", (240, 330), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (20, 20, 140), 3)
    cv2.putText(aadhaar_img, "Mera Aadhaar, Meri Pehchan", (240, 370), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
    
    aadhaar_img[450:458, :, :] = (40, 110, 240)
    aadhaar_img[458:466, :, :] = (255, 255, 255)
    aadhaar_img[466:475, :, :] = (60, 160, 40)
    cv2.imwrite("static/samples/sample_clean_aadhaar.jpg", aadhaar_img)
    
    # 2. Tampered PAN Card
    face2_doc = draw_synthetic_face(seed=202, gender="male", skin_tone=(190, 160, 135), hair_color=(50, 35, 25))
    face2_selfie = draw_synthetic_face(seed=202, gender="male", skin_tone=(190, 160, 135), hair_color=(50, 35, 25))
    cv2.imwrite("static/samples/selfie_person2.jpg", face2_selfie)
    
    pan_img = np.ones((480, 750, 3), dtype=np.uint8) * 248
    pan_img[:, :] = (240, 250, 250)
    cv2.rectangle(pan_img, (0, 0), (750, 75), (210, 230, 245), -1)
    cv2.putText(pan_img, "INCOME TAX DEPARTMENT", (180, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (10, 50, 100), 2)
    cv2.putText(pan_img, "GOVT. OF INDIA", (280, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (10, 50, 100), 2)
    
    face2_resized = cv2.resize(face2_doc, (140, 170))
    pan_img[120:290, 50:190] = face2_resized
    cv2.rectangle(pan_img, (50, 120), (190, 290), (140, 140, 140), 2)
    
    cv2.putText(pan_img, "Permanent Account Number Card", (220, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
    cv2.putText(pan_img, "Name: ROHIT SHARMA", (220, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    cv2.putText(pan_img, "Father's Name: SURESH SHARMA", (220, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)
    cv2.putText(pan_img, "DOB: 22/03/1990", (220, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    
    # Tampering Patch
    cv2.rectangle(pan_img, (215, 275), (550, 335), (255, 255, 255), -1)
    cv2.rectangle(pan_img, (215, 275), (550, 335), (200, 200, 200), 2)
    cv2.putText(pan_img, "ABCDE9999Z", (230, 320), cv2.FONT_HERSHEY_DUPLEX, 1.1, (10, 10, 10), 3)
    
    noise = np.random.normal(0, 40, (60, 335, 3)).astype(np.int16)
    patch = pan_img[275:335, 215:550].astype(np.int16) + noise
    pan_img[275:335, 215:550] = np.clip(patch, 0, 255).astype(np.uint8)
    cv2.imwrite("static/samples/sample_tampered_pan.jpg", pan_img)
    
    # 3. Face Mismatch
    face3_doc = draw_synthetic_face(seed=303, gender="female", skin_tone=(235, 205, 185), hair_color=(70, 30, 20))
    face3_mismatch = draw_synthetic_face(seed=888, gender="male", skin_tone=(175, 140, 110), hair_color=(15, 15, 15))
    cv2.imwrite("static/samples/selfie_mismatch.jpg", face3_mismatch)
    
    passport_img = np.ones((480, 750, 3), dtype=np.uint8) * 255
    cv2.rectangle(passport_img, (0, 0), (750, 70), (40, 40, 90), -1)
    cv2.putText(passport_img, "PASSPORT - REPUBLIC OF INDIA", (150, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    
    face3_resized = cv2.resize(face3_doc, (140, 170))
    passport_img[110:280, 50:190] = face3_resized
    cv2.rectangle(passport_img, (50, 110), (190, 280), (120, 120, 120), 2)
    
    cv2.putText(passport_img, "Surname: KAPOOR", (220, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(passport_img, "Given Name: PRIYA", (220, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(passport_img, "Passport No: Z8741923", (220, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 120), 2)
    cv2.putText(passport_img, "DOB: 15/07/1995", (220, 235), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(passport_img, "Expiry Date: 20/05/2032", (220, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    
    cv2.rectangle(passport_img, (20, 360), (730, 450), (240, 240, 240), -1)
    cv2.putText(passport_img, "P<INDKAPOOR<<PRIYA<<<<<<<<<<<<<<<<<<<<<<<<<", (30, 395), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)
    cv2.putText(passport_img, "Z8741923<4IND9507152F3205208<<<<<<<<<<<<<<<", (30, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 30, 30), 2)
    cv2.imwrite("static/samples/sample_face_mismatch_doc.jpg", passport_img)
    
    # 4. Poor Quality DL
    face4_doc = draw_synthetic_face(seed=404, gender="male", skin_tone=(215, 190, 165), hair_color=(25, 25, 35))
    face4_selfie = draw_synthetic_face(seed=404, gender="male", skin_tone=(215, 190, 165), hair_color=(25, 25, 35))
    cv2.imwrite("static/samples/selfie_person4.jpg", face4_selfie)
    
    dl_img = np.ones((480, 750, 3), dtype=np.uint8) * 245
    cv2.rectangle(dl_img, (0, 0), (750, 65), (100, 100, 110), -1)
    cv2.putText(dl_img, "UNION OF INDIA - DRIVING LICENCE", (130, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2)
    face4_resized = cv2.resize(face4_doc, (140, 170))
    dl_img[110:280, 50:190] = face4_resized
    cv2.rectangle(dl_img, (50, 110), (190, 280), (120, 120, 120), 2)
    cv2.putText(dl_img, "Name: MANISH GUPTA", (220, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2)
    cv2.putText(dl_img, "DL No: DL-0420190087654", (220, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(dl_img, "DOB: 10/01/1998", (220, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    cv2.putText(dl_img, "Valid Upto: 10/01/2038", (220, 255), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (20, 20, 20), 2)
    
    blurred = cv2.GaussianBlur(dl_img, (15, 15), 9)
    darkened = (blurred.astype(np.float32) * 0.45).astype(np.uint8)
    cv2.imwrite("static/samples/sample_poor_quality_dl.jpg", darkened)

if __name__ == "__main__":
    create_sample_suite()
