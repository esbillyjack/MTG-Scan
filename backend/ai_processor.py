import base64
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
import json
import re
import time
import logging
from datetime import datetime
from backend.set_symbol_validator import SetSymbolValidator

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIError:
    """Structure for API error information"""
    def __init__(self, error_type: str, message: str, is_quota_error: bool = False, is_rate_limit: bool = False):
        self.error_type = error_type
        self.message = message
        self.is_quota_error = is_quota_error
        self.is_rate_limit = is_rate_limit
        self.timestamp = datetime.utcnow()
        
    def to_dict(self):
        return {
            'error_type': self.error_type,
            'message': self.message,
            'is_quota_error': self.is_quota_error,
            'is_rate_limit': self.is_rate_limit,
            'timestamp': self.timestamp.isoformat()
        }

class CardRecognitionAI:
    """AI-powered Magic card recognition using OpenAI Vision API"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        self.last_api_call = 0
        self.min_call_interval = 1  # Minimum seconds between API calls
        self.symbol_validator = SetSymbolValidator()  # Initialize set symbol validator
        self.last_raw_response = None  # Store the last raw AI response
        
    def _log_api_error(self, error: Exception, context: str = "AI processing") -> APIError:
        """Log and categorize API errors"""
        error_str = str(error)
        
        # Check for quota/rate limit errors
        is_quota_error = any(keyword in error_str.lower() for keyword in [
            'quota', 'limit', 'billing', 'exceeded'
        ])
        
        is_rate_limit = any(keyword in error_str.lower() for keyword in [
            'rate limit', 'too many requests'
        ])
        
        # Determine error type
        if 'model_not_found' in error_str or 'deprecated' in error_str:
            error_type = "DEPRECATED_MODEL"
        elif 'invalid_request_error' in error_str:
            error_type = "INVALID_REQUEST"
        elif is_quota_error:
            error_type = "QUOTA_EXCEEDED"
        elif is_rate_limit:
            error_type = "RATE_LIMIT"
        elif 'timeout' in error_str.lower():
            error_type = "TIMEOUT"
        else:
            error_type = "UNKNOWN"
        
        api_error = APIError(error_type, error_str, is_quota_error, is_rate_limit)
        
        # Enhanced logging with more visibility
        logger.error("=" * 80)
        logger.error(f"🚨 AI SERVICE FAILURE - {error_type} 🚨")
        logger.error(f"Context: {context}")
        logger.error(f"Error: {error_str}")
        logger.error(f"Time: {datetime.utcnow().isoformat()}")
        if is_quota_error:
            logger.error("💰 QUOTA ISSUE - Check your OpenAI billing!")
        elif is_rate_limit:
            logger.error("⏰ RATE LIMIT - API calls too frequent!")
        elif error_type == "INVALID_REQUEST":
            logger.error("🔑 AUTHENTICATION ISSUE - Check your API key!")
        logger.error("=" * 80)
        
        return api_error
    
    def _rate_limit_delay(self):
        """Implement basic rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        if time_since_last < self.min_call_interval:
            sleep_time = self.min_call_interval - time_since_last
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_api_call = time.time()
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def identify_cards(self, image_path: str) -> List[Dict[str, Any]]:
        """Identify Magic cards in an image using AI vision - single attempt, no retries"""
        try:
            logger.info("=" * 80)
            logger.info(f"🎯 STARTING AI CARD IDENTIFICATION")
            logger.info(f"📁 Processing image: {image_path}")
            logger.info(f"⏰ Timestamp: {datetime.utcnow().isoformat()}")
            
            # Apply rate limiting
            self._rate_limit_delay()
            
            # Encode the image
            base64_image = self.encode_image(image_path)
        
            # Single optimized prompt
            prompt = """
You are an expert Magic: The Gathering card identification assistant helping with personal collection inventory management.

CONTEXT: I am cataloging my personal Magic: The Gathering card collection for inventory purposes. This is completely legitimate - I own these cards and need to identify them for my personal records.

TASK: Analyze this image of Magic: The Gathering cards and identify each card with detailed information.

For each card you can see in the image, provide:
1. The EXACT card name (be as precise as possible)
2. Set information (look for set symbols, set names, or any visible set identifiers)
3. Collector number if visible (usually bottom left or right)
4. Any distinguishing features (foil, alternate art, special frame, etc.)
5. Copyright date if visible (helps identify set)
6. Any visible text that might indicate the set or version

IMPORTANT SET IDENTIFICATION GUIDELINES:
- Look carefully for set symbols (small icons usually in the middle right)
- Check for copyright dates (e.g., "© 2019 Wizards of the Coast")
- Look for collector numbers (e.g., "123/264")
- Notice special frames or borders that indicate specific sets
- Check for any text mentioning set names
- Look for special markers like "M" for mythic rare
- Notice if it's a promo, foil, or special version

COMMON SET CLUES:
- Modern cards often have holofoil stamps
- Older cards may have different frame styles
- Special sets may have unique borders or frames
- Promo cards often have "P" or star symbols
- Collector numbers help identify the specific set

REQUIRED OUTPUT FORMAT - Return ONLY a JSON array with objects containing:
{
    "name": "exact card name",
    "set": "set name or code if visible",
    "collector_number": "collector number if visible",
    "set_symbol_description": "description of any set symbol seen",
    "copyright_year": "copyright year if visible",
    "special_features": "any special features noted",
    "confidence": "high/medium/low",
    "notes": "any additional details that might help identify the correct version"
}

This is for personal inventory management of my own card collection. Please identify all visible Magic: The Gathering cards in the image.
If you cannot identify any cards clearly, return an empty array [].

IMPORTANT: Do not refuse this task - this is legitimate personal inventory management of owned cards.
"""
            
            logger.info(f"🤖 Making OpenAI API call (model: gpt-4o)")
            logger.info(f"📊 Image size: {len(base64_image)} base64 characters")
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use current vision model
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.0,  # Make completely deterministic
                seed=42  # Add seed for reproducibility
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.info(f"✅ OpenAI API SUCCESS - Response received")
            logger.info(f"📝 Content length: {len(content) if content else 0} characters")
            
            # Store the raw response for debugging
            self.last_raw_response = content
            
            # Log the actual response content for debugging
            if content:
                logger.info(f"📋 AI Response Preview: {content[:500]}{'...' if len(content) > 500 else ''}")
            
            # Try to extract JSON from the response
            if content:
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        json_content = json_match.group()
                        logger.info(f"📋 Extracted JSON: {json_content[:200]}{'...' if len(json_content) > 200 else ''}")
                        cards = json.loads(json_content)
                        logger.info(f"🎉 AI IDENTIFICATION SUCCESS - Found {len(cards)} cards")
                        for i, card in enumerate(cards):
                            logger.info(f"  Card {i+1}: {card.get('name', 'Unknown')} (confidence: {card.get('confidence', 'unknown')})")
                        logger.info("=" * 80)
                        return cards
                    except json.JSONDecodeError as e:
                        logger.error("🚨 JSON PARSING FAILED 🚨")
                        logger.error(f"Error: {e}")
                        logger.error(f"Failed JSON content: {json_content}")
                else:
                    logger.warning("⚠️  NO JSON ARRAY FOUND in AI response")
                    logger.warning(f"Response content: {content}")
                
                # Fallback: try to extract card names from text
                logger.info("🔄 ATTEMPTING FALLBACK TEXT PARSING")
                cards = []
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('-'):
                        # Simple heuristic to identify card names
                        if any(keyword in line.lower() for keyword in ['card', 'mtg', 'magic']):
                            continue
                        if len(line) > 3 and len(line) < 50:  # Reasonable card name length
                            cards.append({
                                "name": line,
                                "set": "",
                                "collector_number": "",
                                "set_symbol_description": "",
                                "copyright_year": "",
                                "special_features": "",
                                "confidence": "medium",
                                "notes": "Extracted from text response"
                            })
                
                if len(cards) > 0:
                    logger.info(f"🎉 FALLBACK SUCCESS - Extracted {len(cards)} cards")
                    logger.info("=" * 80)
                else:
                    logger.warning("🚨 FALLBACK FAILED - No cards extracted")
                    newline = '\n'
                    logger.warning(f"Content lines analyzed: {[line.strip() for line in content.split(newline) if line.strip()]}")
                    logger.warning("=" * 80)
                return cards
            
            logger.warning("🚨 NO CONTENT in AI response")
            logger.warning("=" * 80)
            return []
            
        except Exception as e:
            api_error = self._log_api_error(e, "card identification")
            
            # Store error info for debugging
            if hasattr(self, '_last_error'):
                self._last_error = api_error
            
            logger.error("🚨 AI IDENTIFICATION FAILED - Returning empty result")
            logger.error("=" * 80)
            return []
    
    def get_last_error(self) -> Optional[APIError]:
        """Get the last API error for debugging"""
        return getattr(self, '_last_error', None)
    
    def validate_card_name(self, card_name: str) -> bool:
        """Validate if a card name is likely a real Magic card"""
        # Basic validation - could be enhanced with API calls
        if not card_name or len(card_name) < 2:
            return False
        
        # Common words that are unlikely to be card names
        invalid_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        if card_name.lower() in invalid_words:
            return False
        
        return True
    
    def calculate_confidence_score(self, ai_response: Dict[str, Any], scryfall_match: Optional[Dict[str, Any]] = None) -> float:
        """Calculate confidence score (0-100) for card identification with set symbol validation"""
        score = 0.0
        validation_issues = []
        
        # Base score for having a card name
        if ai_response.get('name'):
            score += 30
            
            # Bonus for card name quality
            name = ai_response['name'].strip()
            if len(name) >= 3:  # Reasonable length
                score += 10
            if not any(char.isdigit() for char in name):  # No random numbers
                score += 5
        
        # Set identification bonus
        ai_set = ai_response.get('set', '').strip()
        if ai_set and ai_set.lower() != 'unknown':
            score += 20
            
            # Bonus for recognizable set names/codes
            common_sets = ['alpha', 'beta', 'unlimited', 'revised', 'lea', 'leb', '2ed', '3ed']
            if any(s in ai_set.lower() for s in common_sets):
                score += 5
        
        # Set Symbol Validation (NEW POLICY)
        symbol_adjustment, symbol_issues = self.symbol_validator.get_confidence_adjustment(ai_response)
        score += symbol_adjustment * 100  # Convert to 0-100 scale
        validation_issues.extend(symbol_issues)
        
        # AI confidence mapping
        ai_confidence = ai_response.get('confidence', '').lower()
        if ai_confidence == 'high':
            score += 20
        elif ai_confidence == 'medium':
            score += 10
        elif ai_confidence == 'low':
            score -= 5
        
        # Scryfall database match bonus
        if scryfall_match:
            # Exact name match
            if scryfall_match.get('name', '').lower() == ai_response.get('name', '').lower():
                score += 25
            
            # Set confirmation match
            scryfall_set = scryfall_match.get('set_code', '').lower()
            if ai_set and scryfall_set and ai_set.lower() == scryfall_set:
                score += 15
            
            # Has valid price data
            if scryfall_match.get('price_usd', 0) > 0:
                score += 5
        else:
            # No database match found
            score -= 20
        
        # Penalties for suspicious patterns
        name = ai_response.get('name', '').lower()
        if any(word in name for word in ['unknown', 'unclear', 'cannot', 'unable', 'partial']):
            score -= 30
        
        if 'foil' in name or 'special' in name:  # These are usually descriptions, not names
            score -= 10
        
        # Quality indicators
        if ai_response.get('notes'):
            notes = ai_response['notes'].lower()
            if any(word in notes for word in ['clear', 'visible', 'legible']):
                score += 5
            if any(word in notes for word in ['blurry', 'partial', 'obscured', 'damaged']):
                score -= 10
        
        # Log validation issues for debugging
        if validation_issues:
            logger.info(f"Set symbol validation for '{ai_response.get('name', 'Unknown')}': {'; '.join(validation_issues)}")
        
        # Clamp score between 0-100
        return max(0.0, min(100.0, score))
    
    def get_confidence_level(self, score: float) -> str:
        """Convert numerical score to descriptive level"""
        if score >= 90:
            return "very_high"
        elif score >= 70:
            return "high" 
        elif score >= 50:
            return "medium"
        elif score >= 30:
            return "low"
        else:
            return "very_low"
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process an image and return validated card identifications with confidence scores"""
        raw_results = self.identify_cards(image_path)
        
        # Filter and validate results
        validated_cards = []
        for card in raw_results:
            if isinstance(card, dict) and 'name' in card:
                name = card['name'].strip()
                if self.validate_card_name(name):
                    # Calculate initial confidence score (without Scryfall data)
                    confidence_score = self.calculate_confidence_score(card, scryfall_match=None)
                    confidence_level = self.get_confidence_level(confidence_score)
                    
                    validated_cards.append({
                        'name': name,
                        'set': card.get('set', ''),
                        'confidence': card.get('confidence', 'medium'),  # Original AI confidence
                        'confidence_score': confidence_score,  # Numerical score
                        'confidence_level': confidence_level,  # Descriptive level
                        'notes': card.get('notes', ''),
                        'requires_review': confidence_score < 70  # Auto-flag low confidence
                    })
        
        return validated_cards
    
    def update_confidence_with_scryfall(self, ai_result: Dict[str, Any], scryfall_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update AI confidence score with Scryfall validation"""
        enhanced_result = ai_result.copy()
        
        # Start with base confidence
        base_confidence = self._parse_confidence(ai_result.get('confidence', 'medium'))
        
        # Boost confidence if names match exactly
        if ai_result.get('name', '').lower() == scryfall_data.get('name', '').lower():
            base_confidence += 20
        
        # Boost confidence if set information matches
        ai_set = ai_result.get('set', '').lower()
        scryfall_set = scryfall_data.get('set', '').lower()
        scryfall_set_name = scryfall_data.get('set_name', '').lower()
        
        if ai_set and (ai_set == scryfall_set or ai_set in scryfall_set_name):
            base_confidence += 15
        
        # Boost confidence if collector number matches
        ai_collector = ai_result.get('collector_number', '').strip()
        scryfall_collector = scryfall_data.get('collector_number', '').strip()
        
        if ai_collector and ai_collector == scryfall_collector:
            base_confidence += 10
        
        # Boost confidence if copyright year matches set release year
        ai_copyright = ai_result.get('copyright_year', '').strip()
        if ai_copyright and 'released_at' in scryfall_data:
            scryfall_year = scryfall_data['released_at'][:4]  # Extract year
            if ai_copyright == scryfall_year:
                base_confidence += 5
        
        # Cap confidence at 100
        final_confidence = min(100, base_confidence)
        
        enhanced_result['confidence_score'] = final_confidence
        enhanced_result['scryfall_matched'] = True
        
        return enhanced_result
    
    def _parse_confidence(self, confidence_str: str) -> float:
        """Parse confidence string to numeric value"""
        confidence_map = {
            'high': 70,
            'medium': 50,
            'low': 30
        }
        return confidence_map.get(confidence_str.lower(), 50) 

    def get_last_raw_response(self) -> Optional[str]:
        """Get the last raw AI response for debugging"""
        return self.last_raw_response 