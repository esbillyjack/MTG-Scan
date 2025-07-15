#!/usr/bin/env python3
"""
Vision Processor Factory - Manages multiple vision processing backends
"""

import json
import os
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VisionProcessorBase(ABC):
    """Base class for all vision processors"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', True)
        self.last_failure_time = None
        self.failure_count = 0
        
    @abstractmethod
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process an image and return card information"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get processor name"""
        pass
    
    def is_available(self) -> bool:
        """Check if processor is available for use"""
        return self.enabled
    
    def record_failure(self):
        """Record a failure for this processor"""
        self.last_failure_time = datetime.now()
        self.failure_count += 1
        logger.warning(f"💥 {self.get_name()} processor failed (count: {self.failure_count})")
    
    def record_success(self):
        """Record a success for this processor"""
        if self.failure_count > 0:
            logger.info(f"✅ {self.get_name()} processor recovered after {self.failure_count} failures")
        self.failure_count = 0
        self.last_failure_time = None

class OpenAIVisionProcessor(VisionProcessorBase):
    """OpenAI Vision Processor"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.setup_openai_client()
    
    def setup_openai_client(self):
        """Setup OpenAI client"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable required")
            
            self.client = OpenAI(
                api_key=api_key,
                timeout=self.config.get('timeout', 120),
                max_retries=self.config.get('max_retries', 3)
            )
        except Exception as e:
            logger.error(f"Failed to setup OpenAI client: {e}")
            self.enabled = False
    
    def get_name(self) -> str:
        return "OpenAI"
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process image using OpenAI Vision API"""
        try:
            # Use existing CardRecognitionAI logic
            from backend.ai_processor import CardRecognitionAI
            ai_processor = CardRecognitionAI()
            result = ai_processor.process_image(image_path)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise Exception(f"OpenAI Vision processing failed: {e}")

class ClaudeVisionProcessor(VisionProcessorBase):
    """Claude Vision Processor using Anthropic API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.setup_claude_client()
    
    def setup_claude_client(self):
        """Setup Claude client"""
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable required")
            
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to setup Claude client: {e}")
            logger.warning("Install: pip install anthropic")
            self.enabled = False
    
    def get_name(self) -> str:
        return "Claude Vision"
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process image using Claude Vision API"""
        try:
            import anthropic
            import base64
            
            # Read and encode image
            with open(image_path, 'rb') as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Claude vision prompt
            prompt = """Analyze this Magic: The Gathering card image and identify each card with detailed information.

For each card you can see, provide:
1. The EXACT card name
2. Set information (if visible)
3. Collector number if visible
4. Any distinguishing features
5. Confidence level

Return the results as a JSON array. If no cards can be identified, return an empty array [].

Focus on accuracy - only identify cards you can clearly see and read."""
            
            # Make Claude API call
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Parse response - handle different response formats
            try:
                if hasattr(response, 'content') and response.content:
                    content = response.content[0].text
                else:
                    content = str(response)
            except:
                content = str(response)
            
            # Extract JSON from response
            import re
            import json
            if content:
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    cards = json.loads(json_match.group())
                    self.record_success()
                    return cards
            
            # If no JSON found, return empty array
            logger.warning("No valid JSON found in Claude response")
            self.record_success()
            return []
            
        except Exception as e:
            self.record_failure()
            raise Exception(f"Claude Vision processing failed: {e}")

class GoogleVisionProcessor(VisionProcessorBase):
    """Google Vision Processor with full image analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.setup_google_client()
    
    def setup_google_client(self):
        """Setup Google Vision client"""
        try:
            from google.cloud import vision
            # Google Cloud credentials should be set via environment variable
            # GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
            self.client = vision.ImageAnnotatorClient()
        except Exception as e:
            logger.error(f"Failed to setup Google Vision client: {e}")
            logger.warning("Install: pip install google-cloud-vision")
            self.enabled = False
    
    def get_name(self) -> str:
        return "Google Vision"
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process image using Google Vision API with full analysis"""
        try:
            from google.cloud import vision
            
            # Read image
            with open(image_path, 'rb') as image_file:
                content = image_file.read()
            
            image = vision.Image(content=content)
            
            # Perform multiple types of analysis
            features = [
                vision.Feature(type_=vision.Feature.Type.TEXT_DETECTION),
                vision.Feature(type_=vision.Feature.Type.OBJECT_LOCALIZATION),
                vision.Feature(type_=vision.Feature.Type.LABEL_DETECTION),
            ]
            
            request = vision.AnnotateImageRequest(image=image, features=features)
            response = self.client.annotate_image(request=request)
            
            if response.error.message:
                raise Exception(f"Google Vision API error: {response.error.message}")
            
            # Extract comprehensive image data
            image_analysis = self._extract_image_data(response)
            
            # Use OpenAI to analyze the comprehensive image data for card identification
            cards = self._analyze_vision_data_for_cards(image_analysis)
            
            self.record_success()
            return cards
            
        except Exception as e:
            self.record_failure()
            raise Exception(f"Google Vision processing failed: {e}")
    
    def _extract_image_data(self, response) -> Dict[str, Any]:
        """Extract comprehensive data from Google Vision response"""
        # Extract text
        text_annotations = response.text_annotations
        detected_text = text_annotations[0].description if text_annotations else ""
        
        # Extract objects
        objects = []
        for obj in response.localized_object_annotations:
            objects.append({
                "name": obj.name,
                "confidence": obj.score,
                "bounding_box": {
                    "vertices": [(vertex.x, vertex.y) for vertex in obj.bounding_poly.normalized_vertices]
                }
            })
        
        # Extract labels
        labels = []
        for label in response.label_annotations:
            labels.append({
                "description": label.description,
                "confidence": label.score
            })
        
        return {
            "text": detected_text,
            "objects": objects,
            "labels": labels
        }
    
    def _analyze_vision_data_for_cards(self, image_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze comprehensive vision data to identify Magic cards"""
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return []
            
            client = OpenAI(api_key=api_key, timeout=30)
            
            # Create comprehensive prompt with all vision data
            prompt = f"""Analyze this comprehensive image analysis data from a Magic: The Gathering card image and identify any cards:

TEXT DETECTED:
{image_data['text']}

OBJECTS DETECTED:
{[obj['name'] for obj in image_data['objects']]}

LABELS DETECTED:
{[label['description'] for label in image_data['labels']]}

Based on this multi-modal analysis, identify any Magic: The Gathering cards present. Return a JSON array of cards found with name, set (if identifiable), and confidence level.
If no cards can be identified, return an empty array []."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            import re
            import json
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                cards = json.loads(json_match.group())
                return cards
            
            return []
            
        except Exception as e:
            logger.error(f"Vision data analysis failed: {e}")
            return []
    
    def _analyze_text_for_cards(self, text: str) -> List[Dict[str, Any]]:
        """Analyze extracted text to identify Magic cards"""
        if not text.strip():
            return []
        
        try:
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return []
            
            client = OpenAI(api_key=api_key, timeout=30)
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this text extracted from a Magic: The Gathering card image and identify any card names:

{text}

Return a JSON array of cards found with name, set (if identifiable), and confidence level.
If no cards can be identified, return an empty array []."""
                    }
                ],
                max_tokens=500,
                temperature=0.0
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                import json
                cards = json.loads(json_match.group())
                return cards
            
            return []
            
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return []

class LocalOCRProcessor(VisionProcessorBase):
    """Local OCR Processor using Tesseract"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.setup_tesseract()
    
    def setup_tesseract(self):
        """Setup Tesseract OCR"""
        try:
            import pytesseract
            from PIL import Image
            
            # Set tesseract path if specified
            tesseract_path = self.config.get('tesseract_path')
            if tesseract_path:
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            
        except Exception as e:
            logger.error(f"Failed to setup Tesseract: {e}")
            logger.warning("Install: pip install pytesseract pillow")
            self.enabled = False
    
    def get_name(self) -> str:
        return "Local OCR"
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process image using local OCR"""
        try:
            import pytesseract
            from PIL import Image
            
            # Open and process image
            image = Image.open(image_path)
            
            # Extract text
            text = pytesseract.image_to_string(image)
            
            # Use OpenAI text analysis if enabled
            if self.config.get('use_openai_text_analysis', True):
                cards = self._analyze_text_for_cards(text)
            else:
                cards = self._simple_card_detection(text)
            
            self.record_success()
            return cards
            
        except Exception as e:
            self.record_failure()
            raise Exception(f"Local OCR processing failed: {e}")
    
    def _analyze_text_for_cards(self, text: str) -> List[Dict[str, Any]]:
        """Analyze extracted text using OpenAI"""
        # Same logic as Google Vision processor
        return GoogleVisionProcessor._analyze_text_for_cards(self, text)
    
    def _simple_card_detection(self, text: str) -> List[Dict[str, Any]]:
        """Simple card detection without AI"""
        # Basic pattern matching for card names
        lines = text.split('\n')
        cards = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 3 and len(line) < 50:  # Reasonable card name length
                cards.append({
                    "name": line,
                    "set": "",
                    "confidence": "low",
                    "notes": "Detected via local OCR"
                })
        
        return cards

class VisionProcessorFactory:
    """Factory for managing vision processors"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.processors = {}
        self.current_processor = None
        self.setup_processors()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config {self.config_file}: {e}")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "vision_processor": {
                "primary": "openai",
                "fallback": "local_ocr",
                "processors": {
                    "openai": {"enabled": True},
                    "local_ocr": {"enabled": True}
                }
            },
            "failover": {
                "auto_switch_on_failure": True,
                "retry_primary_after_minutes": 30
            }
        }
    
    def setup_processors(self):
        """Setup all available processors"""
        processor_configs = self.config["vision_processor"]["processors"]
        
        # Setup OpenAI processor
        if "openai" in processor_configs:
            self.processors["openai"] = OpenAIVisionProcessor(processor_configs["openai"])
        
        # Setup Claude processor
        if "claude" in processor_configs:
            self.processors["claude"] = ClaudeVisionProcessor(processor_configs["claude"])
        
        # Setup Google Vision processor
        if "google" in processor_configs:
            self.processors["google"] = GoogleVisionProcessor(processor_configs["google"])
        
        # Setup Local OCR processor
        if "local_ocr" in processor_configs:
            self.processors["local_ocr"] = LocalOCRProcessor(processor_configs["local_ocr"])
        
        # Set primary processor
        primary_name = self.config["vision_processor"]["primary"]
        if primary_name in self.processors and self.processors[primary_name].is_available():
            self.current_processor = self.processors[primary_name]
            logger.info(f"🎯 Primary vision processor: {primary_name}")
        else:
            # Fall back to first available processor
            for name, processor in self.processors.items():
                if processor.is_available():
                    self.current_processor = processor
                    logger.warning(f"🔄 Using fallback processor: {name}")
                    break
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process image with automatic failover"""
        if not self.current_processor:
            raise Exception("No vision processors available")
        
        try:
            logger.info(f"🔍 Processing image with {self.current_processor.get_name()}")
            result = self.current_processor.process_image(image_path)
            return result
            
        except Exception as e:
            logger.error(f"❌ {self.current_processor.get_name()} failed: {e}")
            
            # Try failover if enabled
            if self.config["failover"]["auto_switch_on_failure"]:
                return self._try_failover(image_path)
            else:
                raise e
    
    def _try_failover(self, image_path: str) -> List[Dict[str, Any]]:
        """Try failover processors"""
        current_name = self.current_processor.get_name().lower().replace(" ", "_")
        
        # Get fallback processor
        fallback_name = self.config["vision_processor"]["fallback"]
        
        if fallback_name in self.processors and self.processors[fallback_name].is_available():
            logger.info(f"🔄 Switching to fallback processor: {fallback_name}")
            fallback_processor = self.processors[fallback_name]
            
            try:
                result = fallback_processor.process_image(image_path)
                # Update current processor
                self.current_processor = fallback_processor
                return result
                
            except Exception as e:
                logger.error(f"❌ Fallback processor {fallback_name} also failed: {e}")
        
        # Try any other available processor
        for name, processor in self.processors.items():
            if processor.is_available() and processor != self.current_processor:
                logger.info(f"🔄 Trying alternative processor: {name}")
                try:
                    result = processor.process_image(image_path)
                    self.current_processor = processor
                    return result
                except Exception as e:
                    logger.error(f"❌ Alternative processor {name} failed: {e}")
        
        raise Exception("All vision processors failed")
    
    def get_current_processor_name(self) -> str:
        """Get current processor name"""
        return self.current_processor.get_name() if self.current_processor else "None"
    
    def get_processor_status(self) -> Dict[str, Any]:
        """Get status of all processors"""
        status = {}
        for name, processor in self.processors.items():
            status[name] = {
                "enabled": processor.enabled,
                "available": processor.is_available(),
                "failure_count": processor.failure_count,
                "last_failure": processor.last_failure_time.isoformat() if processor.last_failure_time else None
            }
        return status

# Global factory instance
_factory = None

def get_vision_processor_factory() -> VisionProcessorFactory:
    """Get the global vision processor factory"""
    global _factory
    if _factory is None:
        _factory = VisionProcessorFactory()
    return _factory 