import base64
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
import json
import re

load_dotenv()

class CardRecognitionAI:
    """AI-powered Magic card recognition using OpenAI Vision API"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def identify_cards(self, image_path: str) -> List[Dict[str, Any]]:
        """Identify Magic cards in an image using AI vision"""
        try:
            # Encode the image
            base64_image = self.encode_image(image_path)
            
            # Create the enhanced prompt for better set identification
            prompt = """
            Analyze this image and identify all Magic: The Gathering cards visible with detailed set information.
            
            For each card you identify, provide:
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
            
            Return the results as a JSON array with objects containing:
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
            
            If you cannot identify any cards, return an empty array.
            Focus on accuracy - if you're unsure about set information, indicate that in the confidence level.
            """
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use latest stable model
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
            
            # Try to extract JSON from the response
            if content:
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        cards = json.loads(json_match.group())
                        return cards
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: try to extract card names from text
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
                
                return cards
            
            return []
            
        except Exception as e:
            print(f"Error in card identification: {e}")
            return []
    
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
        """Calculate confidence score (0-100) for card identification"""
        score = 0.0
        
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