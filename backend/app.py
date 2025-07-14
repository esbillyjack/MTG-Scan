from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, Float
from typing import List, Dict, Any
import os
import shutil
from datetime import datetime
import aiofiles
import uuid
import logging
import subprocess
import sys
import json
from pathlib import Path

from backend.database import get_db, init_db, Card, Scan, ScanImage, ScanResult
from backend.ai_processor import CardRecognitionAI
from backend.price_api import ScryfallAPI
from backend.image_quality_validator import ImageQualityValidator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Magic Card Scanner", version="1.0.0")

# Condition multipliers for realistic pricing
CONDITION_MULTIPLIERS = {
    'NM': 1.0,      # Near Mint: 100%
    'LP': 0.85,     # Lightly Played: 85%
    'MP': 0.70,     # Moderately Played: 70%
    'HP': 0.50,     # Heavily Played: 50%
    'DMG': 0.35,    # Damaged: 35%
    'UNKNOWN': 0.85 # Conservative estimate
}

def get_condition_adjusted_price(base_price: float, condition: str) -> float:
    """Calculate condition-adjusted price"""
    multiplier = CONDITION_MULTIPLIERS.get(condition, CONDITION_MULTIPLIERS['UNKNOWN'])
    return base_price * multiplier

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")
# Mount uploads directory to serve scan images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Initialize database
init_db()

# Initialize AI processor
try:
    ai_processor = CardRecognitionAI()
except ValueError as e:
    logger.error(f"AI processor not available: {e}")
    ai_processor = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page with environment-specific styling"""
    async with aiofiles.open("frontend/index.html", mode="r") as f:
        content = await f.read()
    
    # Get environment mode
    env_mode = os.getenv("ENV_MODE", "production")
    
    # Inject environment class into the body tag
    if env_mode == "development":
        content = content.replace('<body>', '<body class="env-development">')
    else:
        content = content.replace('<body>', '<body class="env-production">')
    
    return HTMLResponse(content=content)

@app.get("/api/environment")
async def get_environment():
    """Get current environment information"""
    env_mode = os.getenv("ENV_MODE", "production")
    port = int(os.getenv("PORT", 8000))
    
    return {
        "environment": env_mode,
        "port": port,
        "is_development": env_mode == "development"
    }

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


@app.post("/upload/scan")
async def upload_and_scan(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload files and create a scan session for the new workflow"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    # Validate that at least one file is an image
    valid_files = [f for f in files if f.content_type is not None and f.content_type.startswith("image/")]
    if not valid_files:
        raise HTTPException(status_code=400, detail="No valid image files provided")
    
    try:
        # Step 1: Create a new scan session
        new_scan = Scan(status="PENDING", notes="Scan initiated from upload")
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
        
        # Step 2: Upload files to the scan
        uploaded_images = []
        for file in valid_files:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            unique_filename = f"scan_{new_scan.id}_{uuid.uuid4()}{file_extension}"
            file_path = f"uploads/{unique_filename}"
            
            # Save the file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Create scan image record
            scan_image = ScanImage(
                scan_id=new_scan.id,
                filename=unique_filename,
                original_filename=file.filename or "unknown",
                file_path=file_path
            )
            db.add(scan_image)
            uploaded_images.append({
                "filename": unique_filename,
                "original_filename": file.filename,
                "size": len(content)
            })
        
        # Update scan totals
        new_scan.total_images = len(uploaded_images)
        db.commit()
        
        return {
            "success": True,
            "scan_id": new_scan.id,
            "status": new_scan.status,
            "total_images": new_scan.total_images,
            "uploaded_images": uploaded_images,
            "message": "Scan created and ready for processing"
        }
        
    except Exception as e:
        # Clean up any uploaded files on error
        for img in uploaded_images:
            try:
                if os.path.exists(f"uploads/{img['filename']}"):
                    os.remove(f"uploads/{img['filename']}")
            except:
                pass
        raise HTTPException(status_code=500, detail=f"Error creating scan: {str(e)}")


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
                "scan_id": getattr(card, 'scan_id', None),
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
                "added_method": card.added_method or "LEGACY",
                "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                "last_seen": card.last_seen.isoformat() if card.last_seen else None
            })
        
        result = {
            "view_mode": "stacked",
            "total_stacks": len(grouped_cards),
            "cards": list(grouped_cards.values())
        }
        
        # Debug logging: Print sample card data being sent to frontend
        if grouped_cards:
            sample_card = list(grouped_cards.values())[0]
            logger.info(f"🎯 FRONTEND DEBUG: Sample stacked card data sent to frontend: name='{sample_card['name']}', set_code='{sample_card['set_code']}', set_name='{sample_card['set_name']}'")
        
        return result
    else:
        # Return individual cards
        cards = db.query(Card).filter(Card.deleted == False).order_by(Card.name).all()
        
        result = {
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
                    "count": card.count,
                    "stack_count": card.stack_count,
                    "stack_id": card.stack_id,
                    "scan_id": getattr(card, 'scan_id', None),
                    "first_seen": card.first_seen.isoformat() if card.first_seen else None,
                    "last_seen": card.last_seen.isoformat() if card.last_seen else None,
                    "image_url": card.image_url,
                    "notes": card.notes,
                    "condition": card.condition,
                    "is_example": card.is_example,
                    "duplicate_group": card.duplicate_group,
                    "added_method": card.added_method or "LEGACY"
                }
                for card in cards
            ]
        }
        
        # Debug logging: Print sample card data being sent to frontend
        if cards:
            sample_card = cards[0]
            logger.info(f"🎯 FRONTEND DEBUG: Sample individual card data sent to frontend: name='{sample_card.name}', set_code='{sample_card.set_code}', set_name='{sample_card.set_name}'")
        
        return result

@app.get("/cards/unknown-sets")
async def get_cards_with_unknown_sets(db: Session = Depends(get_db)):
    """Get all cards that have unknown or missing set information"""
    try:
        # Query for cards with missing or unknown set information
        cards = db.query(Card).filter(
            Card.deleted == False,
            or_(
                Card.set_name == None,
                Card.set_name == '',
                Card.set_name.like('%unknown%'),
                Card.set_name.like('%not found%'),
                Card.set_code == None,
                Card.set_code == '',
                Card.set_code.like('%unknown%')
            )
        ).order_by(Card.name).all()
        
        # Convert to dictionaries for JSON response
        cards_data = []
        for card in cards:
            card_dict = {
                'id': card.id,
                'name': card.name,
                'set_name': card.set_name or 'Unknown',
                'set_code': card.set_code or 'UNK',
                'image_url': card.image_url,
                'first_seen': card.first_seen.isoformat() if card.first_seen else None,
                'added_method': card.added_method or 'LEGACY',
                'scan_id': getattr(card, 'scan_id', None)  # Handle missing scan_id gracefully
            }
            cards_data.append(card_dict)
        
        return {
            "success": True,
            "cards": cards_data,
            "count": len(cards_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting cards with unknown sets: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting cards with unknown sets: {str(e)}")

@app.get("/cards/{card_id}")
async def get_card(card_id: int, db: Session = Depends(get_db)):
    """Get specific card details"""
    card = db.query(Card).filter(Card.id == card_id, Card.deleted == False).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    return {
        "id": card.id,
        "unique_id": card.unique_id,
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
        "scan_id": getattr(card, 'scan_id', None),
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
    try:
        # Get total number of unique cards
        total_cards = db.query(Card).filter(Card.deleted == False).count()
        
        # Get total count of all cards (including duplicates)
        total_count = db.query(func.sum(Card.count)).filter(Card.deleted == False).scalar() or 0
        
        # Calculate total value (USD) - simplified calculation
        cards_for_value = db.query(Card).filter(Card.deleted == False).all()
        total_value = sum(
            (card.price_usd or 0) * card.count * get_condition_adjusted_price(1.0, card.condition)
            for card in cards_for_value
        )
        
        # Get counts by rarity
        rarity_counts = db.query(
            Card.rarity,
            func.count(Card.id).label('unique_count'),
            func.sum(Card.count).label('total_count')
        ).filter(Card.deleted == False).group_by(Card.rarity).all()
        
        rarity_stats = {}
        for rarity, unique_count, count in rarity_counts:
            rarity_stats[rarity or 'Unknown'] = {
                'unique_count': unique_count,
                'total_count': count
            }
        
        # Get counts by condition
        condition_counts = db.query(
            Card.condition,
            func.count(Card.id).label('unique_count'),
            func.sum(Card.count).label('total_count')
        ).filter(Card.deleted == False).group_by(Card.condition).all()
        
        condition_stats = {}
        for condition, unique_count, count in condition_counts:
            condition_stats[condition or 'Unknown'] = {
                'unique_count': unique_count,
                'total_count': count
            }
        
        return {
            "total_cards": total_cards,
            "total_count": total_count,
            "total_value_usd": round(total_value, 2),
            "rarity_stats": rarity_stats,
            "condition_stats": condition_stats
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export/local")
async def export_to_local(request_data: dict = None, db: Session = Depends(get_db)):
    """Export card database to local CSV and Excel files"""
    try:
        # Get parameters from request
        file_path = request_data.get('file_path', '') if request_data else ''
        file_format = request_data.get('format', 'csv') if request_data else 'csv'
        overwrite = request_data.get('overwrite', False) if request_data else False
        
        if not file_path:
            raise HTTPException(status_code=400, detail="File path is required")
        
        # Run the export script as a subprocess
        process = subprocess.Popen(
            [sys.executable, 'export_local.py', file_path, file_format, str(overwrite).lower()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate()
        
        logger.info(f"Export stdout: {stdout}")
        if stderr:
            logger.warning(f"Export stderr: {stderr}")
        
        if process.returncode != 0:
            logger.error(f"Export failed with return code {process.returncode}")
            logger.error(f"Export stderr: {stderr}")
            # Return the actual error message from the script
            error_message = stderr.strip() if stderr.strip() else "Export failed"
            raise HTTPException(status_code=500, detail=error_message)
            
        # Parse the JSON response from the export script
        try:
            result = json.loads(stdout)
            if result.get("success"):
                return {
                    "success": True,
                    "message": "Export completed successfully",
                    "file_path": result.get("file_path"),
                    "filename": Path(result.get("file_path", "")).name,
                    "record_count": result.get("record_count", 0),
                    "format": result.get("format", file_format)
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "file_exists": result.get("file_exists", False)
                }
        except json.JSONDecodeError:
            logger.error(f"Failed to parse export script output: {stdout}")
            raise HTTPException(status_code=500, detail="Invalid response from export script")
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# New Scan Management Endpoints

@app.post("/scan/start")
async def start_scan(db: Session = Depends(get_db)):
    """Create a new scan session"""
    new_scan = Scan(status="PENDING", notes="New scan session")
    db.add(new_scan)
    db.commit()
    db.refresh(new_scan)
    
    return {
        "success": True,
        "scan_id": new_scan.id,
        "status": new_scan.status,
        "created_at": new_scan.created_at.isoformat()
    }


@app.post("/scan/{scan_id}/upload")
async def upload_scan_images(scan_id: int, files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload images to a scan session"""
    # Verify scan exists and is in valid state
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    if scan.status not in ["PENDING", "PROCESSING"]:
        raise HTTPException(status_code=400, detail="Scan is not in a state that accepts uploads")
    
    uploaded_images = []
    
    for file in files:
        if not file.content_type.startswith("image/"):
            continue  # Skip non-image files
            
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
        unique_filename = f"scan_{scan_id}_{uuid.uuid4()}{file_extension}"
        file_path = f"uploads/{unique_filename}"
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Create scan image record
        scan_image = ScanImage(
            scan_id=scan_id,
            filename=unique_filename,
            original_filename=file.filename or "unknown",
            file_path=file_path
        )
        db.add(scan_image)
        uploaded_images.append({
            "filename": unique_filename,
            "original_filename": file.filename,
            "size": len(content)
        })
    
    # Update scan totals
    scan.total_images = db.query(ScanImage).filter(ScanImage.scan_id == scan_id).count()
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "uploaded_images": uploaded_images,
        "total_images": scan.total_images
    }


@app.post("/scan/{scan_id}/process")
async def process_scan(scan_id: int, db: Session = Depends(get_db)):
    """Start AI processing of uploaded images"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
        
    if scan.status != "PENDING":
        raise HTTPException(status_code=400, detail="Scan is not ready for processing")
    
    # Update scan status
    scan.status = "PROCESSING"
    db.commit()
    
    try:
        # Get all images for this scan
        scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan_id).all()
        
        total_cards_found = 0
        processed_images = 0
        
        for scan_image in scan_images:
            try:
                # Process image with AI
                if ai_processor:
                    card_results = ai_processor.process_image(scan_image.file_path)
                    
                    # Create scan results for each identified card
                    for card_data in card_results:
                        # Use enhanced Scryfall search with AI set information
                        ai_set_info = card_data.get('set', '') or card_data.get('set_symbol_description', '')
                        scryfall_data = ScryfallAPI.get_card_data(card_data['name'], ai_set_info)
                        
                        # Update confidence with Scryfall data
                        if scryfall_data:
                            enhanced_card = ai_processor.update_confidence_with_scryfall(card_data, scryfall_data)
                        else:
                            enhanced_card = card_data
                            enhanced_card['scryfall_matched'] = False
                            enhanced_card['confidence_score'] = ai_processor._parse_confidence(card_data.get('confidence', 'medium'))
                        
                        # Create scan result
                        import json
                        import ast
                        scan_result = ScanResult(
                            scan_id=scan_id,
                            scan_image_id=scan_image.id,
                            card_name=enhanced_card['name'],
                            set_code=scryfall_data.get('set_code', '') if scryfall_data else enhanced_card.get('set', ''),
                            set_name=scryfall_data.get('set_name', '') if scryfall_data else '',
                            collector_number=scryfall_data.get('collector_number', '') if scryfall_data else enhanced_card.get('collector_number', ''),
                            confidence_score=enhanced_card.get('confidence_score', 0.0),
                            status="PENDING",
                            card_data=json.dumps(scryfall_data) if scryfall_data else json.dumps(enhanced_card),
                            ai_raw_response=ai_processor.get_last_raw_response()  # Store raw AI response
                        )
                        db.add(scan_result)
                        total_cards_found += 1
                    
                    # Update scan image
                    scan_image.cards_found = len(card_results)
                    scan_image.processed_at = datetime.utcnow()
                    
                else:
                    scan_image.processing_error = "AI processor not available"
                
                processed_images += 1
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing scan image {scan_image.id}: {error_msg}")
                scan_image.processing_error = error_msg
                
                # Check if this is an AI service error
                if ai_processor:
                    last_error = ai_processor.get_last_error()
                    if last_error:
                        logger.warning(f"AI service error details - Type: {last_error.error_type}, "
                                     f"Quota: {last_error.is_quota_error}, "
                                     f"Rate limit: {last_error.is_rate_limit}")
                        
                        # Update scan notes with error details for persistent tracking
                        if last_error.is_quota_error or last_error.is_rate_limit:
                            scan.notes = f"API Error: {last_error.error_type} - {last_error.message}"
        
        # Update scan with results
        scan.processed_images = processed_images
        scan.total_cards_found = total_cards_found
        
        # Set status to READY_FOR_REVIEW even if no cards found (for user review of scan quality)
        scan.status = "READY_FOR_REVIEW"
        scan.updated_at = datetime.utcnow()
        
        # Store a note about zero cards found
        if total_cards_found == 0:
            scan.notes = f"Scan completed with 0 cards found. Images stored for future review."
        
        db.commit()
        
        return {
            "success": True,
            "scan_id": scan_id,
            "status": scan.status,
            "processed_images": processed_images,
            "total_cards_found": total_cards_found
        }
        
    except Exception as e:
        # Mark scan as failed
        scan.status = "FAILED"
        scan.notes = f"Processing error: {str(e)}"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: int, db: Session = Depends(get_db)):
    """Get current scan status and progress"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "scan_id": scan.id,
        "status": scan.status,
        "total_images": scan.total_images,
        "processed_images": scan.processed_images,
        "total_cards_found": scan.total_cards_found,
        "unknown_cards_count": scan.unknown_cards_count,
        "created_at": scan.created_at.isoformat(),
        "updated_at": scan.updated_at.isoformat() if scan.updated_at else None
    }


@app.get("/scan/{scan_id}/results")
async def get_scan_results(scan_id: int, db: Session = Depends(get_db)):
    """Get scan results for review"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get all scan results with image info
    results = db.query(ScanResult, ScanImage).join(
        ScanImage, ScanResult.scan_image_id == ScanImage.id
    ).filter(ScanResult.scan_id == scan_id).all()
    
    scan_results = []
    for scan_result, scan_image in results:
        # Parse card data to make it available for the frontend
        card_data = None
        if scan_result.card_data:
            import json
            import ast
            try:
                # Try JSON parsing first
                card_data = json.loads(scan_result.card_data)
            except json.JSONDecodeError:
                try:
                    # If JSON fails, try to evaluate as Python literal
                    card_data = ast.literal_eval(scan_result.card_data)
                except (ValueError, SyntaxError):
                    # If both fail, use None
                    card_data = None
        
        scan_results.append({
            "id": scan_result.id,
            "card_name": scan_result.card_name,
            "set_code": scan_result.set_code,
            "set_name": scan_result.set_name,
            "confidence_score": scan_result.confidence_score,
            "status": scan_result.status,
            "image_filename": scan_image.filename,
            "requires_review": scan_result.confidence_score < 70,
            "created_at": scan_result.created_at.isoformat(),
            "card_data": card_data
        })
    
    return {
        "scan_id": scan_id,
        "scan_status": scan.status,
        "results": scan_results,
        "total_results": len(scan_results)
    }


@app.get("/scan/pending")
async def get_pending_scans(db: Session = Depends(get_db)):
    """Get all scans that need user review"""
    pending_scans = db.query(Scan).filter(
        Scan.status.in_(["READY_FOR_REVIEW", "PROCESSING"])
    ).order_by(Scan.created_at.desc()).all()
    
    return {
        "pending_scans": [
            {
                "id": scan.id,
                "status": scan.status,
                "total_images": scan.total_images,
                "total_cards_found": scan.total_cards_found,
                "created_at": scan.created_at.isoformat()
            }
            for scan in pending_scans
        ]
    }


@app.post("/scan/{scan_id}/accept")
async def accept_scan_results(scan_id: int, request_data: dict, db: Session = Depends(get_db)):
    """Accept specific scan results or all results"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    accept_all = request_data.get('accept_all', False)
    result_ids = request_data.get('result_ids', [])
    
    if accept_all:
        # Accept all pending results
        results_to_accept = db.query(ScanResult).filter(
            ScanResult.scan_id == scan_id,
            ScanResult.status == "PENDING"
        ).all()
    else:
        # Accept specific results
        if not result_ids:
            raise HTTPException(status_code=400, detail="No result IDs provided")
        results_to_accept = db.query(ScanResult).filter(
            ScanResult.scan_id == scan_id,
            ScanResult.id.in_(result_ids),
            ScanResult.status == "PENDING"
        ).all()
    
    accepted_count = 0
    for result in results_to_accept:
        result.status = "ACCEPTED"
        result.decided_at = datetime.utcnow()
        accepted_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "accepted_count": accepted_count
    }


@app.post("/scan/{scan_id}/reject")
async def reject_scan_results(scan_id: int, request_data: dict, db: Session = Depends(get_db)):
    """Reject specific scan results"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result_ids = request_data.get('result_ids', [])
    
    if not result_ids:
        raise HTTPException(status_code=400, detail="No result IDs provided")
    
    results_to_reject = db.query(ScanResult).filter(
        ScanResult.scan_id == scan_id,
        ScanResult.id.in_(result_ids),
        ScanResult.status == "PENDING"
    ).all()
    
    rejected_count = 0
    for result in results_to_reject:
        result.status = "REJECTED"
        result.decided_at = datetime.utcnow()
        rejected_count += 1
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "rejected_count": rejected_count
    }


@app.post("/scan/{scan_id}/commit")
async def commit_scan(scan_id: int, db: Session = Depends(get_db)):
    """Finalize scan by creating cards from accepted results"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get accepted results
    accepted_results = db.query(ScanResult).filter(
        ScanResult.scan_id == scan_id,
        ScanResult.status == "ACCEPTED"
    ).all()
    
    if not accepted_results:
        raise HTTPException(status_code=400, detail="No accepted results to commit")
    
    created_cards = 0
    for result in accepted_results:
        try:
            # Parse card data - handle both JSON string and Python string representation
            import json
            import ast
            
            card_data = {}
            if result.card_data:
                try:
                    # Try JSON parsing first
                    card_data = json.loads(result.card_data)
                except json.JSONDecodeError:
                    try:
                        # If JSON fails, try to evaluate as Python literal
                        card_data = ast.literal_eval(result.card_data)
                    except (ValueError, SyntaxError):
                        # If both fail, use empty dict
                        card_data = {}
            
            # Create duplicate group identifier - prioritize card_data for consistency
            set_name_for_group = card_data.get('set_name') or result.set_name or ''
            collector_number_for_group = card_data.get('collector_number') or result.collector_number or ''
            duplicate_group = f"{result.card_name}|{set_name_for_group}|{collector_number_for_group}"
            
            # Debug logging for set information
            logger.info(f"Creating card '{result.card_name}' with set info: "
                       f"set_code='{card_data.get('set_code') or result.set_code or ''}', "
                       f"set_name='{card_data.get('set_name') or result.set_name or ''}'")
            
            # Check for existing cards in this group
            existing_cards = db.query(Card).filter(Card.duplicate_group == duplicate_group, Card.deleted == False).all()
            
            # Generate stack_id
            if existing_cards:
                stack_id = existing_cards[0].stack_id
                total_count = sum(card.count for card in existing_cards) + 1
                for card in existing_cards:
                    card.stack_count = total_count
            else:
                stack_id = str(uuid.uuid4())
            
            # Create new card - prioritize card_data for set info, fallback to result fields
            new_card = Card(
                name=result.card_name,
                set_code=card_data.get('set_code') or result.set_code or '',
                set_name=card_data.get('set_name') or result.set_name or '',
                collector_number=card_data.get('collector_number') or result.collector_number or '',
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
                count=1,
                stack_count=len(existing_cards) + 1,
                notes=f"Imported from scan {scan_id}",
                condition="LP",
                is_example=False,
                duplicate_group=duplicate_group,
                stack_id=stack_id,
                scan_id=scan_id,
                scan_result_id=result.id,
                import_status="ACCEPTED",
                added_method="SCANNED"
            )
            db.add(new_card)
            created_cards += 1
            
        except Exception as e:
            print(f"Error creating card from result {result.id}: {e}")
            continue
    
    # Update scan status
    scan.status = "COMPLETED"
    scan.updated_at = datetime.utcnow()
    scan.notes = f"Completed: {created_cards} cards imported"
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "status": "COMPLETED",
        "cards_created": created_cards
    }


@app.delete("/scan/{scan_id}")
async def cancel_scan(scan_id: int, db: Session = Depends(get_db)):
    """Cancel a scan and clean up files"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get scan images for cleanup
    scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan_id).all()
    
    # Delete image files
    deleted_files = 0
    for scan_image in scan_images:
        try:
            if os.path.exists(scan_image.file_path):
                os.remove(scan_image.file_path)
                deleted_files += 1
        except Exception as e:
            print(f"Error deleting file {scan_image.file_path}: {e}")
    
    # Update scan status
    scan.status = "CANCELLED"
    scan.updated_at = datetime.utcnow()
    scan.notes = f"Cancelled by user. {deleted_files} files cleaned up."
    
    db.commit()
    
    return {
        "success": True,
        "scan_id": scan_id,
        "status": "CANCELLED",
        "files_deleted": deleted_files
    }


@app.post("/admin/populate-sets")
async def populate_missing_sets(db: Session = Depends(get_db)):
    """Populate missing set information for existing cards"""
    try:
        # Get cards with missing set information
        cards_to_update = db.query(Card).filter(
            Card.deleted == False,
            (Card.set_name.is_(None) | (Card.set_name == '') |
             Card.collector_number.is_(None) | (Card.collector_number == '') |
             Card.image_url.is_(None) | (Card.image_url == ''))
        ).all()
        
        if not cards_to_update:
            return {
                "success": True,
                "message": "All cards already have complete set information",
                "updated_count": 0
            }
        
        updated_count = 0
        for card in cards_to_update:
            try:
                # Get enhanced set data
                missing_data = ScryfallAPI.populate_missing_set_data(card.name, card.set_code)
                
                if missing_data:
                    # Update missing fields
                    if not card.set_name and missing_data.get('set_name'):
                        card.set_name = missing_data['set_name']
                    
                    if not card.collector_number and missing_data.get('collector_number'):
                        card.collector_number = missing_data['collector_number']
                    
                    if not card.image_url and missing_data.get('image_url'):
                        card.image_url = missing_data['image_url']
                    
                    if missing_data.get('rarity'):
                        card.rarity = missing_data['rarity']
                    
                    updated_count += 1
                
                # Be nice to the API
                if updated_count % 10 == 0:
                    db.commit()
                    
            except Exception as e:
                print(f"Error updating card {card.name}: {e}")
                continue
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully populated set information for {updated_count} cards",
            "updated_count": updated_count,
            "total_processed": len(cards_to_update)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error populating sets: {str(e)}")


@app.get("/scan/{scan_id}/details")
async def get_scan_details(scan_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific scan"""
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Get scan images
        scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan.id).all()
        images = []
        for img in scan_images:
            images.append({
                "filename": img.filename,
                "url": f"/{img.filename}"
            })
        
        # Get cards from this scan
        cards = db.query(Card).filter(Card.scan_id == scan.id, Card.deleted == False).all()
        card_list = []
        for card in cards:
            card_list.append({
                "name": card.name,
                "set_name": card.set_name,
                "condition": card.condition
            })
        
        return {
            "success": True,
            "scan": {
                "id": scan.id,
                "status": scan.status,
                "total_images": scan.total_images,
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "images": images,
                "cards": card_list
            }
        }
        
    except Exception as e:
        print(f"Error getting scan details: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scan details: {str(e)}")


@app.put("/scan/result/{result_id}/set")
async def update_scan_result_set(result_id: int, set_data: dict, db: Session = Depends(get_db)):
    """Update the set information for a scan result"""
    try:
        # Get the scan result
        scan_result = db.query(ScanResult).filter(ScanResult.id == result_id).first()
        if not scan_result:
            raise HTTPException(status_code=404, detail="Scan result not found")
        
        # Update the set information
        scan_result.set_code = set_data.get('set_code', '')
        scan_result.set_name = set_data.get('set_name', '')
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Updated scan result {result_id} set to {set_data.get('set_name')}",
            "result": {
                "id": scan_result.id,
                "set_code": scan_result.set_code,
                "set_name": scan_result.set_name
            }
        }
        
    except Exception as e:
        print(f"Error updating scan result set: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating scan result set: {str(e)}")





@app.get("/scan/history")
async def get_scan_history(db: Session = Depends(get_db)):
    """Get all scan history with images and cards found (excluding cancelled scans)"""
    try:
        # Get all scans ordered by newest first, excluding cancelled scans
        scans = db.query(Scan).filter(Scan.status != "CANCELLED").order_by(Scan.created_at.desc()).all()
        
        scan_history = []
        for scan in scans:
            # Get scan images
            scan_images = db.query(ScanImage).filter(ScanImage.scan_id == scan.id).all()
            
            # Get cards created from this scan
            scan_cards = db.query(Card).filter(Card.scan_id == scan.id, Card.deleted == False).all()
            
            # Format images
            images = []
            for image in scan_images:
                images.append({
                    "filename": image.filename,
                    "original_filename": image.original_filename,
                    "file_path": image.file_path
                })
            
            # Format cards
            cards = []
            for card in scan_cards:
                cards.append({
                    "name": card.name,
                    "set_name": card.set_name,
                    "set_code": card.set_code,
                    "collector_number": card.collector_number,
                    "rarity": card.rarity,
                    "count": card.count
                })
            
            scan_data = {
                "id": scan.id,
                "status": scan.status,
                "total_images": scan.total_images,
                "cards_count": len(cards),
                "created_at": scan.created_at.isoformat() if scan.created_at else None,
                "updated_at": scan.updated_at.isoformat() if hasattr(scan, 'updated_at') and scan.updated_at else None,
                "images": images,
                "cards": cards
            }
            
            scan_history.append(scan_data)
        
        return {
            "success": True,
            "total_scans": len(scan_history),
            "scans": scan_history
        }
        
    except Exception as e:
        logger.error(f"Error getting scan history: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scan history: {str(e)}")


@app.get("/debug/ai-health")
async def get_ai_health():
    """Check AI processor health status"""
    if ai_processor is None:
        return {"status": "unavailable", "error": "AI processor not initialized"}
    
    try:
        # Check if OpenAI API key is available
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"status": "error", "error": "OpenAI API key not found"}
        
        # Check last error
        last_error = ai_processor.get_last_error()
        error_info = last_error.to_dict() if last_error else None
        
        return {
            "status": "healthy",
            "api_key_present": bool(api_key),
            "last_error": error_info,
            "rate_limit_interval": ai_processor.min_call_interval
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/debug/ai-errors")
async def get_ai_errors():
    """Get recent AI processing errors"""
    if ai_processor is None:
        return {"error": "AI processor not available"}
    
    last_error = ai_processor.get_last_error()
    if last_error:
        return {
            "has_errors": True,
            "last_error": last_error.to_dict()
        }
    else:
        return {"has_errors": False}

@app.get("/debug/ai-logs-full")
async def get_ai_logs_full():
    """Get complete AI service logs"""
    import logging
    import io
    
    try:
        # Get the logger and its handlers
        ai_logger = logging.getLogger('ai_processor')
        app_logger = logging.getLogger(__name__)
        
        logs_content = []
        
        # Add AI processor information
        if ai_processor:
            logs_content.append("=== AI PROCESSOR STATUS ===")
            logs_content.append(f"Model: gpt-4o")
            logs_content.append(f"Last API Call: {ai_processor.last_api_call}")
            logs_content.append(f"Min Call Interval: {ai_processor.min_call_interval}")
            
            # Add last error if available
            last_error = ai_processor.get_last_error() if hasattr(ai_processor, 'get_last_error') else None
            if last_error:
                logs_content.append("\n=== LAST ERROR ===")
                logs_content.append(f"Type: {last_error.error_type}")
                logs_content.append(f"Message: {last_error.message}")
                logs_content.append(f"Timestamp: {last_error.timestamp}")
                logs_content.append(f"Quota Error: {last_error.is_quota_error}")
                logs_content.append(f"Rate Limit: {last_error.is_rate_limit}")
            
            logs_content.append("\n=== SYSTEM INFORMATION ===")
            logs_content.append(f"Server Time: {datetime.utcnow()}")
            logs_content.append(f"Python Logger Level: {logging.getLogger().level}")
            
        else:
            logs_content.append("AI Processor not available")
        
        return {
            "success": True,
            "logs": "\n".join(logs_content),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting full AI logs: {e}")
        return {
            "success": False,
            "logs": f"Error retrieving logs: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/scan/{scan_id}/info")
async def get_scan_info(scan_id: int, db: Session = Depends(get_db)):
    """Get scan information for rescanning"""
    try:
        # Get the scan record
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Get the first scan image (assuming single image per scan for rescan)
        scan_image = db.query(ScanImage).filter(ScanImage.scan_id == scan_id).first()
        if not scan_image:
            raise HTTPException(status_code=404, detail="Scan image not found")
        
        return {
            "scan_id": scan.id,
            "image_filename": scan_image.filename,
            "status": scan.status,
            "created_at": scan.created_at
        }
        
    except Exception as e:
        logger.error(f"Error getting scan info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scan info: {str(e)}")


@app.post("/validate/image-quality")
async def validate_image_quality(file: UploadFile = File(...)):
    """Validate image quality before AI processing"""
    try:
        # Save uploaded file temporarily
        temp_filename = f"temp_validation_{uuid.uuid4().hex}.jpg"
        temp_path = os.path.join("uploads", temp_filename)
        
        with open(temp_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)
        
        # Initialize validator and validate image
        validator = ImageQualityValidator()
        validation_result = validator.validate_image(temp_path)
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "filename": file.filename,
            "validation": validation_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        
        logger.error(f"Error validating image quality: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating image: {str(e)}")


@app.get("/guidelines/photo")
async def get_photo_guidelines():
    """Get mobile-friendly photo capture guidelines"""
    try:
        validator = ImageQualityValidator()
        guidelines = validator.get_photo_guidelines()
        
        return {
            "guidelines": guidelines,
            "policies": {
                "no_retries": "AI processing runs once per image - no automatic retries",
                "set_symbol_validation": "Set symbols are cross-referenced with known sets for accuracy",
                "collector_numbers": "Collector numbers are processed as-is without validation",
                "confidence_scoring": "Confidence scores include set symbol correlation analysis"
            },
            "tips": [
                "Use good lighting to avoid shadows and glare",
                "Ensure cards are flat and not bent or curved", 
                "Take photos from directly above or at slight angle",
                "Use a contrasting background (dark for light cards, light for dark cards)",
                "Allow some space around cards - don't crop too tightly",
                "For multiple cards, arrange in a grid pattern with clear separation",
                "Tap to focus on the cards before taking the photo",
                "Hold camera steady or use a tripod for sharpest results"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting photo guidelines: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting guidelines: {str(e)}")


@app.get("/scan/policies")
async def get_scan_policies():
    """Get current scan processing policies"""
    return {
        "policies": {
            "retry_policy": {
                "enabled": False,
                "description": "No automatic retries - AI processing runs once per image"
            },
            "set_symbol_correlation": {
                "enabled": True,
                "description": "Set symbols are validated against known set descriptions for confidence scoring"
            },
            "collector_number_processing": {
                "validation": False,
                "description": "Collector numbers are processed as-is without format validation"
            },
            "image_quality_checks": {
                "enabled": True,
                "description": "Images are validated for resolution, focus, and quality before processing"
            }
        },
        "confidence_factors": [
            "Card name clarity and completeness",
            "Set information accuracy", 
            "Set symbol correlation with known sets",
            "Scryfall database match confirmation",
            "Image quality metrics (sharpness, resolution)",
            "AI self-reported confidence level"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/scan/{scan_id}/ai-response")
async def get_scan_ai_response(scan_id: int, db: Session = Depends(get_db)):
    """Get the raw AI response for a scan"""
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get scan results with raw AI responses
    scan_results = db.query(ScanResult).filter(ScanResult.scan_id == scan_id).first()
    if not scan_results:
        return {
            "scan_id": scan_id,
            "has_ai_response": False,
            "message": "No AI response found for this scan"
        }
    
    return {
        "scan_id": scan_id,
        "has_ai_response": bool(scan_results.ai_raw_response),
        "ai_raw_response": scan_results.ai_raw_response or "No raw response stored",
        "created_at": scan_results.created_at.isoformat() if scan_results.created_at else None,
        "cards_found": len(db.query(ScanResult).filter(ScanResult.scan_id == scan_id).all())
    }

@app.post("/api/migrate-from-local")
async def migrate_from_local():
    """
    Emergency migration endpoint to migrate data from local database to current Railway database
    This endpoint can be triggered remotely to populate the Railway database
    """
    try:
        import subprocess
        import os
        
        # Check if we're in a cloud environment
        if not os.getenv("DATABASE_URL"):
            return {"error": "This endpoint only works in cloud environments with DATABASE_URL"}
        
        # This would need the local database file to be uploaded first
        # For now, return the current database info
        from backend.database import engine
        
        # Get database connection info
        db_url = str(engine.url)
        
        return {
            "message": "Migration endpoint ready",
            "current_database": db_url.split('@')[0] + '@[REDACTED]' if '@' in db_url else db_url,
            "instructions": "Upload your local database file first, then trigger migration"
        }
        
    except Exception as e:
        return {"error": f"Migration failed: {str(e)}"}

@app.get("/api/database-info")
async def get_database_info():
    """Get current database connection information"""
    try:
        from backend.database import engine
        from sqlalchemy import text
        
        db_url = str(engine.url)
        
        # Get table counts
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM cards WHERE deleted = false OR deleted IS NULL"))
            card_count = result.scalar()
            
        return {
            "database_url": db_url.split('@')[0] + '@[REDACTED]' if '@' in db_url else db_url,
            "card_count": card_count,
            "database_type": "postgresql" if "postgresql" in db_url else "sqlite"
        }
        
    except Exception as e:
        return {"error": f"Database info failed: {str(e)}"}


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable, default to 8000 for production
    port = int(os.getenv("PORT", 8000))
    
    # Get environment mode
    env_mode = os.getenv("ENV_MODE", "production")
    
    print(f"🚀 Starting Magic Card Scanner Server in {env_mode} mode on port {port}")
    
    uvicorn.run(app, host="0.0.0.0", port=port) 