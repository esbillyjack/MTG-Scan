# Magic Card Scanner

An AI-powered web application that identifies Magic: The Gathering cards from photos and tracks your collection with advanced features like stacking, soft deletion, and detailed card management.

## ✨ Features

### Core Functionality
- **AI Card Recognition**: Upload photos and automatically identify MTG cards using OpenAI Vision API
- **Smart Database Tracking**: Store cards with unique IDs, counts, conditions, and timestamps
- **Real-time Price Integration**: Live price lookup from Scryfall API with USD/EUR pricing
- **Soft Deletion Protection**: Cards are safely marked as deleted, not permanently removed

### Advanced Card Management
- **Individual & Stacked Views**: Toggle between seeing all cards individually or grouped by duplicates
- **Visual Stack Effects**: Stacked cards display with mini-fanned visual effects
- **Condition Tracking**: Track card conditions (Near Mint, Lightly Played, etc.)
- **Example Card System**: Mark cards as examples vs. owned cards
- **Duplicate Grouping**: Intelligent grouping of identical cards

### Modern User Interface
- **Proper Magic Card Proportions**: Cards display in authentic 2.5:3.5 ratio
- **Color-Coded Borders**: Cards show color identity borders (White, Blue, Black, Red, Green, Multicolor, Colorless)
- **Responsive Design**: Works on desktop and mobile devices
- **Drag-and-Drop Upload**: Modern file upload with progress tracking
- **Compact Detail Modals**: Streamlined card detail views with navigation

### Collection Features
- **Search & Filter**: Find cards by name or set
- **Navigation Arrows**: Browse through cards with keyboard/click navigation
- **Statistics Dashboard**: Track total cards, counts, and collection value
- **Set & Rarity Management**: Update card sets and rarities with dropdowns

## 🛠 Tech Stack

- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Frontend**: Modern HTML/CSS/JavaScript with responsive design
- **Database**: SQLite with soft deletion and UUID tracking
- **AI**: OpenAI Vision API for card recognition
- **Price API**: Scryfall API for comprehensive card data
- **Image Processing**: Optimized for Magic card recognition

## 📁 Project Structure

```
magic-card-scanner/
├── backend/
│   ├── app.py              # FastAPI application with soft deletion
│   ├── database.py         # Database models with UUID and soft delete
│   ├── ai_processor.py     # AI card recognition engine
│   └── price_api.py        # Scryfall API integration
├── frontend/
│   ├── index.html          # Modern web interface
│   ├── styles.css          # Magic card themed styling
│   └── script.js           # Advanced frontend logic
├── uploads/                # Temporary image storage
├── venv/                   # Python virtual environment
├── migrate_database.py     # Database migration script
├── run.py                  # Application launcher
├── setup.py                # Easy setup script
├── requirements.txt        # Python dependencies
└── README.md              # This documentation
```

## 🚀 Quick Start

### Option 1: Easy Setup (Recommended)
```bash
cd magic-card-scanner
python setup.py
source venv/bin/activate
python run.py
```

### Option 2: Manual Setup
1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Setup**:
   Create `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Database Migration** (if upgrading):
   ```bash
   python migrate_database.py
   ```

5. **Run Application**:
   ```bash
   python run.py
   ```

6. **Access Interface**:
   Open http://localhost:8000 in your browser

## 📖 Usage Guide

### Uploading Cards
1. **Upload Photos**: Drag and drop or click to upload images containing Magic cards
2. **AI Processing**: System identifies all visible cards automatically
3. **Review Results**: See identified cards with prices, sets, and rarities
4. **Auto-Save**: Cards are automatically added to your collection database

### Managing Your Collection
- **Individual View**: See every card separately with counts
- **Stacked View**: Group duplicate cards with visual stack effects
- **Search**: Find cards by name or set using the search bar
- **Edit Details**: Click cards to modify condition, rarity, set, and notes

### Navigation
- **Gallery Browsing**: Click any card to view detailed information
- **Arrow Navigation**: Use left/right arrows to browse through cards
- **Stack Expansion**: Click stacked cards to see all individual copies
- **Modal Details**: Compact, scrollable detail views with all card information

### Safety Features
- **Soft Deletion**: Deleted cards are marked as deleted, not permanently removed
- **Unique Tracking**: Every entry has a UUID for tracking
- **Data Protection**: Multiple safeguards prevent accidental data loss

## 🔌 API Endpoints

### Card Management
- `POST /upload` - Upload and process card images
- `GET /cards?view_mode=individual|stacked` - Get cards with view mode
- `GET /cards/{card_id}` - Get specific card details
- `PUT /cards/{card_id}` - Update card information
- `DELETE /cards/{card_id}` - Soft delete a card (safe)
- `POST /cards` - Add new card manually

### Statistics
- `GET /stats` - Collection statistics and values

### Static Files
- `GET /` - Main web interface
- `GET /styles.css` - Styling
- `GET /script.js` - Frontend functionality

## 🎨 Card Display Features

### Visual Elements
- **Magic Card Proportions**: Authentic 2.5:3.5 aspect ratio
- **Color Identity Borders**: 6px borders matching Magic color identity
- **Mini-Fan Effects**: Stacked cards show realistic fanned appearance
- **Example Badges**: Clear marking of example vs. owned cards
- **Count Displays**: Consistent "Count: X" labeling

### Layout Improvements
- **No Image Cutoff**: Cards display with proper top/bottom positioning
- **Compact Info Sections**: Card names and counts below images
- **Responsive Grid**: Adapts to different screen sizes
- **Optimized Spacing**: 25% more compact detail views

## 🔄 Recent Updates

### Database Improvements
- Added unique UUID for every card entry
- Implemented soft deletion for data safety
- Enhanced indexing for better performance
- Migration script for existing databases

### UI/UX Enhancements
- Fixed Magic card proportions (2.5:3.5 ratio)
- Eliminated image cutoff issues
- Compact detail modals (25% height reduction)
- Improved color border visibility
- Consistent terminology throughout

### Technical Improvements
- Proper navigation context handling
- Enhanced error handling and validation
- Optimized database queries with soft delete filtering
- Improved mobile responsiveness

## 🛡️ Data Safety

The application includes multiple layers of data protection:
- **Soft Deletion**: Cards are never permanently deleted
- **Unique IDs**: Every entry has a UUID for tracking
- **Migration Scripts**: Safe database updates
- **Backup-Friendly**: SQLite database can be easily backed up

## 🔮 Future Enhancements

- **Mana Symbol Display**: Convert text mana costs to Magic symbols
- **Advanced Set Detection**: Improve unknown set/rarity handling
- **Bulk Operations**: Multi-card selection and operations
- **Collection Analytics**: Advanced statistics and trends
- **Export Features**: PDF/CSV collection reports
- **Mobile App**: Native mobile application
- **Deck Building**: Integrate with deck building tools

## 📄 License

This project is for personal use and Magic: The Gathering card collection management.

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve the Magic Card Scanner! 