from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
import os
import shutil
from datetime import datetime
import aiofiles
import uuid

from database import get_db, init_db, Card
from ai_processor import CardRecognitionAI
from price_api import ScryfallAPI

# Initialize FastAPI app
app = FastAPI(title="Magic Card Scanner", version="1.0.0")

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Initialize database
init_db()

# Initialize AI processor
try:
    ai_processor = CardRecognitionAI()
except ValueError as e:
    print(f"Warning: AI processor not available: {e}")
    ai_processor = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    async with aiofiles.open("frontend/index.html", mode="r") as f:
        content = await f.read()
    return HTMLResponse(content=content)

@app.post("/upload")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and process an image to identify Magic cards"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Process image with AI
        if ai_processor is None:
            raise HTTPException(status_code=500, detail="AI processor not available")
        
        identified_cards = ai_processor.process_image(file_path)
        
        # Process each identified card
        results = []
        for card_info in identified_cards:
            card_name = card_info['name']
            
            # Get card data from Scryfall
            card_data = ScryfallAPI.get_card_data(card_name)
            
            if card_data:
                # Create duplicate group identifier
                duplicate_group = f"{card_data['name']}|{card_data.get('set_code', '')}|{card_data.get('collector_number', '')}"
                
                # Check if this card already exists in the database
                existing_cards = db.query(Card).filter(Card.duplicate_group == duplicate_group, Card.deleted == False).all()
                
                # Generate stack_id (use existing one if available, otherwise create new)
                if existing_cards:
                    stack_id = existing_cards[0].stack_id
                    # Update stack_count for all cards in this group
                    total_count = sum(card.count for card in existing_cards) + 1
                    for card in existing_cards:
                        card.stack_count = total_count
                else:
                    stack_id = str(uuid.uuid4())
                
                # Create new card entry (always create separate entry for duplicates)
                new_card = Card(
                    name=card_data['name'],
                    set_code=card_data['set_code'],
                    set_name=card_data['set_name'],
                    collector_number=card_data['collector_number'],
                    rarity=card_data['rarity'],
                    mana_cost=card_data['mana_cost'],
                    type_line=card_data['type_line'],
                    oracle_text=card_data['oracle_text'],
                    flavor_text=card_data['flavor_text'],
                    power=card_data['power'],
                    toughness=card_data['toughness'],
                    colors=card_data['colors'],
                    image_url=card_data['image_url'],
                    price_usd=card_data['price_usd'],
                    price_eur=card_data['price_eur'],
                    price_tix=card_data['price_tix'],
                    count=1,
                    stack_count=len(existing_cards) + 1,
                    notes="",
                    condition="LP", # Changed default condition to LP
                    is_example=False,
                    duplicate_group=duplicate_group,
                    stack_id=stack_id
                )
                db.add(new_card)
                db.commit()
                
                results.append({
                    "name": new_card.name,
                    "set_name": new_card.set_name,
                    "price_usd": new_card.price_usd,
                    "price_eur": new_card.price_eur,
                    "count": new_card.count,
                    "status": "new",
                    "duplicate_group": new_card.duplicate_group
                })
            else:
                # Card not found in Scryfall
                results.append({
                    "name": card_name,
                    "set_name": "",
                    "price_usd": 0.0,
                    "price_eur": 0.0,
                    "count": 0,
                    "status": "not_found",
                    "error": "Card not found in database"
                })
        
        # Clean up uploaded file
        os.remove(file_path)
        
        return {
            "success": True,
            "cards_found": len(identified_cards),
            "cards_processed": len(results),
            "results": results
        }
        
    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/cards")
async def get_cards(db: Session = Depends(get_db), view_mode: str = "individual"):
    """
    Get all cards in the database
    view_mode: "individual" (show all cards) or "stacked" (group duplicates)
    """
    if view_mode == "stacked":
        # Group cards by duplicate_group and return aggregated data
        cards = db.query(Card).filter(Card.deleted == False).order_by(Card.name).all()
        
        # Group by duplicate_group
        grouped_cards = {}
        for card in cards:
            group_key = card.duplicate_group or f"{card.name}|{card.set_code}|{card.collector_number}"
            if group_key not in grouped_cards:
                grouped_cards[group_key] = {
                    "stack_id": card.stack_id,
                    "name": card.name,
                    "set_name": card.set_name,
                    "set_code": card.set_code,
                    "collector_number": card.collector_number,
                    "rarity": card.rarity,
                    "mana_cost": card.mana_cost,
                    "type_line": card.type_line,
                    "oracle_text": card.oracle_text,
                    "flavor_text": card.flavor_text,
                    "power": card.power,
                    "toughness": card.toughness,
                    "colors": card.colors,
                    "price_usd": card.price_usd,
                    "price_eur": card.price_eur,
                    "price_tix": card.price_tix,
                    "count": card.count,  # Add individual card count
                    "stack_count": 0,  # Will sum all counts
                    "total_cards": 0,  # Number of individual card entries
                    "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                    "last_seen": card.last_seen.isoformat() if card.last_seen else None,
                    "image_url": card.image_url,
                    "duplicate_group": card.duplicate_group,
                    "is_example": card.is_example,
                    "duplicates": []
                }
            
            grouped_cards[group_key]["stack_count"] += card.count
            grouped_cards[group_key]["total_cards"] += 1
            grouped_cards[group_key]["duplicates"].append({
                "id": card.id,
                "count": card.count,
                "condition": card.condition,
                "notes": card.notes,
                "is_example": card.is_example,
                "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                "last_seen": card.last_seen.isoformat() if card.last_seen else None
            })
        
        return {
            "view_mode": "stacked",
            "total_stacks": len(grouped_cards),
            "cards": list(grouped_cards.values())
        }
    else:
        # Return individual cards
        cards = db.query(Card).filter(Card.deleted == False).order_by(Card.name).all()
        
        return {
            "view_mode": "individual",
            "total_cards": len(cards),
            "cards": [
                {
                    "id": card.id,
                    "name": card.name,
                    "set_name": card.set_name,
                    "set_code": card.set_code,
                    "collector_number": card.collector_number,
                    "rarity": card.rarity,
                    "price_usd": card.price_usd,
                    "price_eur": card.price_eur,
                    "price_tix": card.price_tix,
                    "count": card.count,
                    "stack_count": card.stack_count,
                    "stack_id": card.stack_id,
                    "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                    "last_seen": card.last_seen.isoformat() if card.last_seen else None,
                    "image_url": card.image_url,
                    "notes": card.notes,
                    "condition": card.condition,
                    "is_example": card.is_example,
                    "duplicate_group": card.duplicate_group
                }
                for card in cards
            ]
        }

@app.get("/cards/{card_id}")
async def get_card(card_id: int, db: Session = Depends(get_db)):
    """Get specific card details"""
    card = db.query(Card).filter(Card.id == card_id, Card.deleted == False).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return {
        "id": card.id,
        "name": card.name,
        "set_code": card.set_code,
        "set_name": card.set_name,
        "collector_number": card.collector_number,
        "rarity": card.rarity,
        "mana_cost": card.mana_cost,
        "type_line": card.type_line,
        "oracle_text": card.oracle_text,
        "flavor_text": card.flavor_text,
        "power": card.power,
        "toughness": card.toughness,
        "colors": card.colors,
        "image_url": card.image_url,
        "price_usd": card.price_usd,
        "price_eur": card.price_eur,
        "price_tix": card.price_tix,
        "count": card.count,
        "notes": card.notes,
        "condition": card.condition,
        "is_example": card.is_example,
        "duplicate_group": card.duplicate_group,
        "first_seen": card.first_seen.isoformat() if card.first_seen else None,
        "last_seen": card.last_seen.isoformat() if card.last_seen else None
    }

@app.put("/cards/{card_id}")
async def update_card(card_id: int, card_data: dict, db: Session = Depends(get_db)):
    """Update card details"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Update allowed fields
    if 'notes' in card_data:
        card.notes = card_data['notes']
    if 'condition' in card_data:
        card.condition = card_data['condition']
    if 'is_example' in card_data:
        card.is_example = card_data['is_example']
    if 'count' in card_data:
        card.count = card_data['count']
    
    db.commit()
    return {"success": True, "card_id": card.id}

@app.post("/cards/{card_id}/increment")
async def increment_card(card_id: int, db: Session = Depends(get_db)):
    """Increment the count for a specific card"""
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    card.count += 1
    card.last_seen = datetime.utcnow()
    db.commit()
    
    return {"success": True, "new_count": card.count}

@app.post("/cards")
async def add_card(card_data: dict, db: Session = Depends(get_db)):
    """Add a new card to the database"""
    try:
        # Create duplicate group identifier
        duplicate_group = f"{card_data['name']}|{card_data.get('set_code', '')}|{card_data.get('collector_number', '')}"
        
        # Create new card (always create separate entry)
        new_card = Card(
            name=card_data['name'],
            set_code=card_data.get('set_code', ''),
            set_name=card_data.get('set_name', ''),
            collector_number=card_data.get('collector_number', ''),
            rarity=card_data.get('rarity', ''),
            mana_cost=card_data.get('mana_cost', ''),
            type_line=card_data.get('type_line', ''),
            oracle_text=card_data.get('oracle_text', ''),
            flavor_text=card_data.get('flavor_text', ''),
            power=card_data.get('power', ''),
            toughness=card_data.get('toughness', ''),
            colors=card_data.get('colors', ''),
            image_url=card_data.get('image_url', ''),
            price_usd=card_data.get('price_usd', 0.0),
            price_eur=card_data.get('price_eur', 0.0),
            price_tix=card_data.get('price_tix', 0.0),
            count=card_data.get('count', 1),
            notes=card_data.get('notes', ''),
            condition=card_data.get('condition', 'LP'),
            is_example=card_data.get('is_example', False),
            duplicate_group=duplicate_group,
            first_seen=datetime.fromisoformat(card_data.get('first_seen', datetime.utcnow().isoformat())),
            last_seen=datetime.fromisoformat(card_data.get('last_seen', datetime.utcnow().isoformat()))
        )
        db.add(new_card)
        db.commit()
        return {"success": True, "status": "created", "card_id": new_card.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding card: {str(e)}")

@app.delete("/cards/{card_id}")
async def delete_card(card_id: int, db: Session = Depends(get_db)):
    """Soft delete a specific card"""
    card = db.query(Card).filter(Card.id == card_id, Card.deleted == False).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Soft delete - just mark as deleted
    card.deleted = True
    card.deleted_at = datetime.utcnow()
    db.commit()
    return {"success": True, "card_id": card_id}

@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    total_cards = db.query(Card).count()
    total_count = db.query(Card).with_entities(func.sum(Card.count)).scalar() or 0
    total_value_usd = db.query(Card).with_entities(func.sum(Card.price_usd * Card.count)).scalar() or 0
    total_value_eur = db.query(Card).with_entities(func.sum(Card.price_eur * Card.count)).scalar() or 0
    
    # Filter out example cards for owned statistics
    owned_cards = db.query(Card).filter(Card.is_example == False).count()
    owned_count = db.query(Card).filter(Card.is_example == False).with_entities(func.sum(Card.count)).scalar() or 0
    owned_value_usd = db.query(Card).filter(Card.is_example == False).with_entities(func.sum(Card.price_usd * Card.count)).scalar() or 0
    owned_value_eur = db.query(Card).filter(Card.is_example == False).with_entities(func.sum(Card.price_eur * Card.count)).scalar() or 0
    
    return {
        "total_unique_cards": total_cards,
        "total_card_count": total_count,
        "total_value_usd": round(total_value_usd, 2),
        "total_value_eur": round(total_value_eur, 2),
        "owned_unique_cards": owned_cards,
        "owned_card_count": owned_count,
        "owned_value_usd": round(owned_value_usd, 2),
        "owned_value_eur": round(owned_value_eur, 2)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 