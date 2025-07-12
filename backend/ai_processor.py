import base64
import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

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
            
            # Create the prompt for card identification
            prompt = """
            Analyze this image and identify all Magic: The Gathering cards visible.
            
            For each card you identify, provide:
            1. The exact card name
            2. The set/edition if visible
            3. Any distinguishing features (foil, special art, etc.)
            
            Focus on:
            - Card names (be as precise as possible)
            - Set symbols or names if visible
            - Multiple cards if present
            - Partial cards if only part is visible
            
            Return the results as a JSON array with objects containing:
            {
                "name": "exact card name",
                "set": "set name if visible",
                "confidence": "high/medium/low",
                "notes": "any additional details"
            }
            
            If you cannot identify any cards, return an empty array.
            """
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
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
                max_tokens=1000,
                temperature=0.1
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON array in the response
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
                            "confidence": "medium",
                            "notes": "Extracted from text response"
                        })
            
            return cards
            
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
    
    def process_image(self, image_path: str) -> List[Dict[str, Any]]:
        """Process an image and return validated card identifications"""
        raw_results = self.identify_cards(image_path)
        
        # Filter and validate results
        validated_cards = []
        for card in raw_results:
            if isinstance(card, dict) and 'name' in card:
                name = card['name'].strip()
                if self.validate_card_name(name):
                    validated_cards.append({
                        'name': name,
                        'set': card.get('set', ''),
                        'confidence': card.get('confidence', 'medium'),
                        'notes': card.get('notes', '')
                    })
        
        return validated_cards 