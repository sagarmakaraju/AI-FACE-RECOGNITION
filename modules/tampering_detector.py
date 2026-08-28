import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import os
import io

class TamperingDetector:
    def __init__(self, quality=90, ela_scale=15):
        self.quality = quality
        self.ela_scale = ela_scale

    def compute_ela(self, image_path):
        """
        Computes Error Level Analysis (ELA) map by measuring JPEG recompression difference
        """
        original = Image.open(image_path).convert('RGB')
        
        # Save to memory buffer at specified JPEG quality
        buffer = io.BytesIO()
        original.save(buffer, 'JPEG', quality=self.quality)
        buffer.seek(0)
        
        recompressed = Image.open(buffer)
        
        # Calculate absolute difference
        ela_img = ImageChops.difference(original, recompressed)
        
        # Calculate extrema
        extrema = ela_img.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff
        
        # Enhance difference image
        ela_enhanced = ImageEnhance.Brightness(ela_img).enhance(min(scale, self.ela_scale))
        ela_np = np.array(ela_enhanced)
        
        # Convert to grayscale error magnitude
        ela_gray = cv2.cvtColor(ela_np, cv2.COLOR_RGB2GRAY)
        return ela_np, ela_gray

    def analyze_noise_inconsistency(self, gray_img):
        """
        Analyzes spatial noise variance irregularities across 16x16 blocks
        """
        h, w = gray_img.shape
        block_size = 16
        variances = []
        
        for y in range(0, h - block_size, block_size):
            for x in range(0, w - block_size, block_size):
                block = gray_img[y:y+block_size, x:x+block_size]
                var_val = float(np.var(block))
                # Only analyze textured/non-empty blocks
                if var_val > 8.0:
                    variances.append(var_val)
                
        if len(variances) < 10:
            return 0.0, 0.0
            
        variances = np.array(variances)
        mean_var = float(np.mean(variances))
        std_var = float(np.std(variances))
        
        # Detect outlier blocks with extreme variance (> 3x mean)
        outlier_blocks = np.sum(variances > (mean_var * 2.8))
        outlier_ratio = (outlier_blocks / len(variances)) * 100.0
        
        noise_ratio = (std_var / (mean_var + 1e-5)) * 5.0 + (outlier_ratio * 4.0)
        return min(noise_ratio, 100.0), std_var

    def analyze_edge_discontinuities(self, gray_img):
        """
        Computes Sobel gradient anomalies to detect spliced boundaries
        """
        sobelx = cv2.Sobel(gray_img, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray_img, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(sobelx**2 + sobely**2)
        
        p98 = np.percentile(gradient_mag, 98)
        p50 = np.percentile(gradient_mag, 50)
        ratio = (p98 / (p50 + 1e-5))
        
        edge_score = (ratio / 35.0) * 20.0
        return min(edge_score, 100.0), float(p98)

    def generate_forensic_heatmap(self, orig_bgr, ela_gray, output_path):
        """
        Combines ELA and gradient anomalies into a false-color forensic heatmap overlay
        """
        h, w = orig_bgr.shape[:2]
        ela_resized = cv2.resize(ela_gray, (w, h))
        
        norm_ela = cv2.normalize(ela_resized, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
        norm_ela = cv2.GaussianBlur(norm_ela, (7, 7), 0)
        
        heatmap = cv2.applyColorMap(norm_ela, cv2.COLORMAP_JET)
        blended = cv2.addWeighted(orig_bgr, 0.60, heatmap, 0.40, 0)
        
        cv2.imwrite(output_path, blended)
        return output_path

    def analyze(self, image_path, heatmap_output_path=None):
        """
        Executes full forensic tampering analysis pipeline
        """
        orig_bgr = cv2.imread(image_path)
        if orig_bgr is None:
            raise ValueError(f"Could not load image at {image_path}")
            
        gray = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2GRAY)
        
        # 1. ELA Analysis
        ela_rgb, ela_gray = self.compute_ela(image_path)
        ela_mean = float(np.mean(ela_gray))
        ela_max = float(np.max(ela_gray))
        
        # 2. Localized ELA anomaly hotspots (> 3.2x mean or > 90 intensity)
        high_threshold = max(ela_mean * 3.2, 90.0)
        anomalous_pixel_pct = float((np.sum(ela_gray > high_threshold) / (ela_gray.size + 1e-5)) * 100.0)
        
        # 3. Noise Inconsistency Analysis
        noise_ratio, noise_std = self.analyze_noise_inconsistency(gray)
        
        # 4. Edge Discontinuity Analysis
        edge_score, grad_p98 = self.analyze_edge_discontinuities(gray)
        
        # 5. Tampering Score Calculation
        # Clean images have low anomalous pixels and uniform noise
        ela_component = min(anomalous_pixel_pct * 12.0, 45.0)
        noise_component = min(noise_ratio * 0.45, 35.0)
        edge_component = min(edge_score * 0.8, 20.0)
        
        raw_score = ela_component + noise_component + edge_component
        tampering_score = round(float(np.clip(raw_score, 0.0, 100.0)), 1)
        
        # 6. Classification
        if tampering_score < 25.0:
            classification = "Normal"
        elif tampering_score < 55.0:
            classification = "Review"
        else:
            classification = "Suspicious"
            
        # 7. Forensic Indicators
        indicators = []
        if anomalous_pixel_pct > 2.0:
            indicators.append(f"Localized JPEG compression anomaly detected ({round(anomalous_pixel_pct, 1)}% hotspot area)")
        if noise_ratio > 30.0:
            indicators.append("Spatial noise irregularity detected across document regions (splicing/patching)")
        if edge_score > 15.0:
            indicators.append("Discontinuous boundary gradients detected around document fields")
            
        if len(indicators) == 0:
            indicators.append("Image compression, sensor noise, and edge gradients appear uniform and authentic.")
            
        # 8. Forensic Heatmap
        heatmap_filename = None
        if heatmap_output_path:
            self.generate_forensic_heatmap(orig_bgr, ela_gray, heatmap_output_path)
            heatmap_filename = os.path.basename(heatmap_output_path)
            
        return {
            "tampering_score": tampering_score,
            "classification": classification,
            "forensic_heatmap": heatmap_filename,
            "metrics": {
                "ela_mean": round(ela_mean, 2),
                "ela_max": round(ela_max, 2),
                "anomalous_pixel_percentage": round(anomalous_pixel_pct, 2),
                "noise_inconsistency_ratio": round(noise_ratio, 2),
                "edge_discontinuity_score": round(edge_score, 2)
            },
            "suspicious_indicators": indicators
        }
