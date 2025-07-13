#!/usr/bin/env python3
"""
Image Quality Validator - Checks image quality before AI processing
"""

import os
from PIL import Image, ImageFilter
from typing import Dict, List, Tuple, Optional, Any
import logging

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

logger = logging.getLogger(__name__)

class ImageQualityValidator:
    """Validates image quality for optimal card scanning"""
    
    def __init__(self):
        # Quality thresholds
        self.min_resolution = (800, 600)      # Minimum width x height
        self.ideal_resolution = (1920, 1080)  # Ideal resolution
        self.max_file_size_mb = 10             # Maximum file size in MB
        self.min_sharpness = 10.0              # Minimum sharpness score
        self.ideal_sharpness = 50.0            # Ideal sharpness score
        
    def validate_image(self, image_path: str) -> Dict[str, Any]:
        """
        Comprehensive image quality validation
        
        Returns:
            {
                'is_valid': bool,
                'quality_score': float (0-100),
                'issues': List[str],
                'recommendations': List[str],
                'details': Dict[str, any]
            }
        """
        if not os.path.exists(image_path):
            return {
                'is_valid': False,
                'quality_score': 0.0,
                'issues': ['Image file not found'],
                'recommendations': ['Please upload a valid image file'],
                'details': {}
            }
        
        try:
            # Load image
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Gather basic info
                width, height = img.size
                file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
                
                # Run all quality checks
                resolution_score, resolution_issues, resolution_recs = self._check_resolution(width, height)
                size_score, size_issues, size_recs = self._check_file_size(file_size_mb)
                sharpness_score, sharpness_issues, sharpness_recs = self._check_sharpness(img)
                aspect_score, aspect_issues, aspect_recs = self._check_aspect_ratio(width, height)
                
                # Calculate overall quality score
                quality_score = (
                    resolution_score * 0.3 +
                    size_score * 0.1 +
                    sharpness_score * 0.4 +
                    aspect_score * 0.2
                )
                
                # Collect all issues and recommendations
                all_issues = resolution_issues + size_issues + sharpness_issues + aspect_issues
                all_recommendations = resolution_recs + size_recs + sharpness_recs + aspect_recs
                
                # Determine if image is valid for processing
                is_valid = (
                    quality_score >= 50.0 and  # Minimum quality threshold
                    width >= self.min_resolution[0] and
                    height >= self.min_resolution[1] and
                    file_size_mb <= self.max_file_size_mb
                )
                
                return {
                    'is_valid': is_valid,
                    'quality_score': quality_score,
                    'issues': all_issues,
                    'recommendations': all_recommendations,
                    'details': {
                        'resolution': f"{width}x{height}",
                        'file_size_mb': round(file_size_mb, 2),
                        'resolution_score': resolution_score,
                        'size_score': size_score,
                        'sharpness_score': sharpness_score,
                        'aspect_score': aspect_score
                    }
                }
                
        except Exception as e:
            logger.error(f"Error validating image {image_path}: {e}")
            return {
                'is_valid': False,
                'quality_score': 0.0,
                'issues': [f'Error processing image: {str(e)}'],
                'recommendations': ['Please try uploading a different image'],
                'details': {}
            }
    
    def _check_resolution(self, width: int, height: int) -> Tuple[float, List[str], List[str]]:
        """Check image resolution"""
        issues = []
        recommendations = []
        
        # Calculate resolution score
        min_w, min_h = self.min_resolution
        ideal_w, ideal_h = self.ideal_resolution
        
        if width < min_w or height < min_h:
            score = 0.0
            issues.append(f"Resolution too low: {width}x{height} (minimum: {min_w}x{min_h})")
            recommendations.append("Use a higher resolution camera or move closer to the cards")
        elif width >= ideal_w and height >= ideal_h:
            score = 100.0
        else:
            # Linear interpolation between minimum and ideal
            w_ratio = (width - min_w) / (ideal_w - min_w)
            h_ratio = (height - min_h) / (ideal_h - min_h)
            score = min(w_ratio, h_ratio) * 100.0
            
            if score < 80:
                recommendations.append("Consider using a higher resolution for better card detail recognition")
        
        return score, issues, recommendations
    
    def _check_file_size(self, file_size_mb: float) -> Tuple[float, List[str], List[str]]:
        """Check file size"""
        issues = []
        recommendations = []
        
        if file_size_mb > self.max_file_size_mb:
            score = 50.0  # Still usable but not ideal
            issues.append(f"File size large: {file_size_mb:.1f}MB (max recommended: {self.max_file_size_mb}MB)")
            recommendations.append("Consider compressing the image or reducing quality to improve upload speed")
        elif file_size_mb < 0.1:
            score = 30.0
            issues.append("File size very small - image may be over-compressed")
            recommendations.append("Use a higher quality setting when taking photos")
        else:
            score = 100.0
            
        return score, issues, recommendations
    
    def _check_sharpness(self, img: Image.Image) -> Tuple[float, List[str], List[str]]:
        """Check image sharpness using Laplacian variance"""
        issues = []
        recommendations = []
        
        try:
            # Convert to grayscale for sharpness analysis
            gray = img.convert('L')
            
            # Resize for faster processing if too large
            if gray.size[0] > 1000 or gray.size[1] > 1000:
                gray.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
            
            # Apply Laplacian filter to detect edges
            laplacian = gray.filter(ImageFilter.Kernel((3, 3), [-1, -1, -1, -1, 8, -1, -1, -1, -1], 1, 0))
            
            # Calculate variance (higher variance = sharper image)
            if HAS_NUMPY:
                np_array = np.array(laplacian)
                sharpness = np_array.var()
            else:
                # Fallback sharpness calculation without numpy
                pixels = list(laplacian.getdata())
                mean = sum(pixels) / len(pixels)
                variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
                sharpness = variance
            
            # Convert to score
            if sharpness < self.min_sharpness:
                score = 0.0
                issues.append(f"Image appears blurry (sharpness: {sharpness:.1f})")
                recommendations.append("Ensure camera is focused properly and hold steady while taking photos")
            elif sharpness >= self.ideal_sharpness:
                score = 100.0
            else:
                score = (sharpness / self.ideal_sharpness) * 100.0
                if score < 70:
                    recommendations.append("Try to get a sharper focus on the cards for better recognition")
            
            return score, issues, recommendations
            
        except Exception as e:
            logger.warning(f"Could not calculate sharpness: {e}")
            return 50.0, [], ["Could not analyze image sharpness"]
    
    def _check_aspect_ratio(self, width: int, height: int) -> Tuple[float, List[str], List[str]]:
        """Check if aspect ratio is reasonable for card photos"""
        issues = []
        recommendations = []
        
        aspect_ratio = width / height
        
        # Good aspect ratios for card photos (landscape or portrait)
        ideal_ratios = [4/3, 3/2, 16/9, 3/4, 2/3, 9/16]  # Including inverses
        
        # Find closest ideal ratio
        closest_ratio = min(ideal_ratios, key=lambda x: abs(x - aspect_ratio))
        ratio_diff = abs(aspect_ratio - closest_ratio)
        
        if ratio_diff < 0.1:
            score = 100.0
        elif ratio_diff < 0.3:
            score = 80.0
        elif ratio_diff < 0.5:
            score = 60.0
            recommendations.append("Consider adjusting the framing for better card visibility")
        else:
            score = 40.0
            issues.append(f"Unusual aspect ratio: {aspect_ratio:.2f}")
            recommendations.append("Try to frame the cards more naturally (avoid very wide or very narrow images)")
        
        return score, issues, recommendations
    
    def get_photo_guidelines(self) -> Dict[str, Any]:
        """Get mobile-friendly photo guidelines"""
        return {
            'resolution': {
                'minimum': f"{self.min_resolution[0]}x{self.min_resolution[1]}",
                'recommended': f"{self.ideal_resolution[0]}x{self.ideal_resolution[1]}",
                'description': "Higher resolution captures more card details"
            },
            'distance': {
                'recommendation': "6-12 inches from cards",
                'description': "Close enough to read text, far enough to avoid blur"
            },
            'lighting': {
                'recommendation': "Good, even lighting without glare",
                'description': "Natural light works best, avoid direct flash on shiny cards"
            },
            'focus': {
                'recommendation': "Tap screen to focus on cards before taking photo",
                'description': "Sharp focus is critical for accurate text recognition"
            },
            'angle': {
                'recommendation': "Take photo straight down or at slight angle",
                'description': "Avoid extreme angles that distort card text"
            },
            'background': {
                'recommendation': "Use contrasting background (dark surface for light cards)",
                'description': "Helps AI distinguish cards from background"
            },
            'layout': {
                'recommendation': "Arrange cards in grid, avoid overlapping",
                'description': "Each card should be clearly separated and visible"
            }
        } 