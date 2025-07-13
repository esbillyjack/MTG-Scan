// Global variables
let cards = [];
let searchTerm = '';
let currentCardIndex = 0;
let viewMode = 'individual'; // 'individual' or 'stacked'
let currentScan = null;
let scanPollingInterval = null;
let fileInputBusy = false; // Flag to prevent multiple file input clicks

// DOM elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const resultsSection = document.getElementById('resultsSection');
const resultsGrid = document.getElementById('resultsGrid');
const cardsGrid = document.getElementById('cardsGrid');
const searchInput = document.getElementById('searchInput');
const loadingOverlay = document.getElementById('loadingOverlay');
const cardModal = document.getElementById('cardModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DEBUG: DOMContentLoaded fired, initializing application');
    setupEventListeners();
    loadCards();
    loadStats();
    addTestData(); // Add test data with real Magic cards
    console.log('🚀 DEBUG: Application initialization complete');
});

// Setup event listeners
function setupEventListeners() {
    console.log('🎧 DEBUG: setupEventListeners called');
    console.log('🎧 DEBUG: fileInput element:', fileInput);
    console.log('🎧 DEBUG: uploadArea element:', uploadArea);
    
    // File upload handling - separate handlers for area and button
    const uploadBtn = document.getElementById('uploadBtn');
    
    // Upload button click handler
    if (uploadBtn) {
        uploadBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event bubbling to upload area
            
            // Check if file input is busy
            if (fileInputBusy) {
                console.log('🔘 DEBUG: File input busy, ignoring button click');
                return;
            }
            
            console.log('🔘 DEBUG: Upload button clicked, triggering file input click');
            fileInputBusy = true;
            fileInput.click();
        });
    }
    
    // Upload area click handler (only if not clicking the button)
    uploadArea.addEventListener('click', (e) => {
        // Only trigger if we didn't click the button (avoid double firing)
        if (e.target !== uploadBtn && !uploadBtn.contains(e.target)) {
            // Check if file input is busy
            if (fileInputBusy) {
                console.log('📎 DEBUG: File input busy, ignoring area click');
                return;
            }
            
            console.log('📎 DEBUG: Upload area clicked, triggering file input click');
            fileInputBusy = true;
            fileInput.click();
        }
    });
    
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    console.log('🎧 DEBUG: Adding change event listener to file input');
    fileInput.addEventListener('change', handleFileSelect);
    
    // Search functionality
    searchInput.addEventListener('input', handleSearch);
    
    // Stack toggle functionality
    const stackToggle = document.getElementById('stackToggle');
    if (stackToggle) { // Check if stackToggle exists
        stackToggle.addEventListener('change', handleStackToggle);
    }
    
    // Modal close handling
    cardModal.addEventListener('click', (e) => {
        if (e.target === cardModal) {
            closeModal();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            // Priority 1: If scanning modal is open, offer to cancel scan
            const scanningModal = document.getElementById('scanningModal');
            if (scanningModal && scanningModal.style.display === 'block') {
                if (currentScan && currentScan.phase === 'processing') {
                    // During processing, Escape cancels the scan
                    cancelScan();
                } else {
                    // During other phases, Escape closes the modal
                    closeScanningModal();
                }
            }
            // Priority 2: If scan history modal is open, close it
            else {
                const scanHistoryModal = document.getElementById('scanHistoryModal');
                if (scanHistoryModal && scanHistoryModal.style.display === 'flex') {
                    closeScanHistoryModal();
                }
                // Priority 3: Close fan overlay if it's open
                else {
                    const fanOverlay = document.getElementById('fanOverlay');
                    if (fanOverlay && fanOverlay.style.display === 'block') {
                        closeFanOverlay();
                    } else {
                        closeModal();
                    }
                }
            }
        } else if (e.key === 'ArrowLeft') {
            navigateCard(-1);
        } else if (e.key === 'ArrowRight') {
            navigateCard(1);
        }
    });
    
    // Add click outside to close fan overlay
    const fanOverlay = document.getElementById('fanOverlay');
    if (fanOverlay) {
        fanOverlay.addEventListener('click', (e) => {
            if (e.target === fanOverlay) {
                closeFanOverlay();
            }
        });
    }
    
    console.log('🎧 DEBUG: setupEventListeners completed');
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    // Check if file input is busy
    if (fileInputBusy) {
        console.log('🗂️ DEBUG: File input busy, ignoring drop');
        return;
    }
    
    const files = e.dataTransfer.files;
    fileInputBusy = true;
    processFiles(files);
}

function handleFileSelect(e) {
    console.log('🔍 DEBUG: handleFileSelect called');
    console.log('🔍 DEBUG: Event target:', e.target);
    console.log('🔍 DEBUG: Event type:', e.type);
    console.log('🔍 DEBUG: Files selected:', e.target.files.length);
    
    const files = e.target.files;
    
    // Only process if files were actually selected (not cancelled)
    if (files && files.length > 0) {
        console.log('🔍 DEBUG: Processing files...', Array.from(files).map(f => f.name));
        processFiles(files);
    } else {
        console.log('🔍 DEBUG: No files selected (user cancelled or no files), ignoring');
        // Reset the file input to ensure clean state
        resetFileInput();
        // Reset busy flag since user cancelled
        fileInputBusy = false;
    }
}

// Reset file input to allow selecting the same files again
function resetFileInput() {
    console.log('🔄 DEBUG: resetFileInput called');
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        console.log('🔄 DEBUG: Resetting file input value');
        // Use a small delay to ensure the file input is properly reset
        setTimeout(() => {
            fileInput.value = '';
            fileInputBusy = false; // Reset busy flag
            console.log('🔄 DEBUG: File input reset complete');
        }, 100);
    } else {
        console.log('🔄 DEBUG: File input not found!');
        fileInputBusy = false; // Reset busy flag even if input not found
    }
}

// Process uploaded files using new scan workflow
async function processFiles(files) {
    console.log('📁 DEBUG: processFiles called with', files.length, 'files');
    
    if (files.length === 0) {
        console.log('📁 DEBUG: No files to process, returning early');
        return;
    }
    
    // Prevent multiple uploads if one is already in progress
    if (currentScan && currentScan.phase !== 'complete') {
        console.log('📁 DEBUG: Scan already in progress, ignoring new upload');
        console.log('📁 DEBUG: Current scan state:', currentScan);
        return;
    }
    
    console.log('📁 DEBUG: Starting file processing...');
    
    // Filter image files
    const imageFiles = Array.from(files).filter(file => 
        file.type.startsWith('image/')
    );
    
    console.log('📁 DEBUG: Filtered to', imageFiles.length, 'image files');
    
    if (imageFiles.length === 0) {
        console.log('📁 DEBUG: No image files found, showing alert');
        alert('Please upload only image files.');
        return;
    }
    
    try {
        console.log('📁 DEBUG: Starting uploadAndScan...');
        // Start the new scan workflow
        const scanResult = await uploadAndScan(imageFiles);
        
        if (scanResult.success) {
            console.log('📁 DEBUG: Scan created successfully:', scanResult);
            // Reset file input after successful scan creation
            resetFileInput();
            // Open scanning modal and start the workflow (non-blocking)
            await showScanningModal(scanResult.scan_id, imageFiles);
        } else {
            console.log('📁 DEBUG: Scan creation failed:', scanResult.error);
            alert(`Error starting scan: ${scanResult.error}`);
            resetFileInput();
        }
        
    } catch (error) {
        console.error('📁 DEBUG: Error in processFiles:', error);
        alert('Error starting scan. Please try again.');
        resetFileInput();
    }
}

// Upload files and create scan session
async function uploadAndScan(files) {
    const formData = new FormData();
    
    // Add all files to the form data
    files.forEach(file => {
        formData.append('files', file);
    });
    
    try {
        const response = await fetch('/upload/scan', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            let errorMessage = 'Failed to upload files';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorMessage;
            } catch (e) {
                const errorText = await response.text();
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        
        const result = await response.json();
        
        // Ensure we have a valid scan_id
        if (!result.scan_id) {
            throw new Error('Server did not return a valid scan ID');
        }
        
        return { success: true, scan_id: result.scan_id, ...result };
    } catch (error) {
        console.error('Upload error:', error);
        return { success: false, error: error.message };
    }
}

// Display upload results
function displayResults(results) {
    if (!results || results.length === 0) {
        resultsSection.style.display = 'none';
        return;
    }
    
    resultsSection.style.display = 'block';
    resultsGrid.innerHTML = '';
    
    results.forEach(card => {
        const cardElement = createResultCard(card);
        resultsGrid.appendChild(cardElement);
    });
}

// Create a result card element
function createResultCard(card) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card-item';
    
    const statusClass = `status-${card.status}`;
    const statusText = card.status === 'new' ? 'New' : 
                      card.status === 'updated' ? 'Updated' : 'Not Found';
    
    cardDiv.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
        </div>
        <div class="card-info">
            <div class="card-name">
                ${card.name}
                <span class="${statusClass}">${statusText}</span>
            </div>
            <div class="card-set">${card.set_name || 'Unknown Set'}</div>
            <div class="card-prices">
                <span class="price price-usd">
                    <i class="fas fa-dollar-sign"></i>
                    $${(card.price_usd || 0).toFixed(2)}
                </span>
                <span class="price price-eur">
                    <i class="fas fa-euro-sign"></i>
                    €${(card.price_eur || 0).toFixed(2)}
                </span>
            </div>
            <div class="card-count">Count: ${card.count || 0}</div>
        </div>
    `;
    
    return cardDiv;
}

// Handle stack toggle
function handleStackToggle() {
    viewMode = document.getElementById('stackToggle').checked ? 'stacked' : 'individual';
    loadCards();
}

// Load cards from database
async function loadCards() {
    try {
        const response = await fetch(`/cards?view_mode=${viewMode}`);
        if (!response.ok) {
            throw new Error('Failed to load cards');
        }
        
        const data = await response.json();
        cards = data.cards || [];
        
        displayCards();
        updateStats(data);
    } catch (error) {
        console.error('Error loading cards:', error);
        cards = [];
        displayCards();
    }
}

// Display cards in the grid
function displayCards() {
    cardsGrid.innerHTML = '';
    
    const filteredCards = filterCards();
    
    if (viewMode === 'stacked') {
        // In stacked mode, show mini-fanned stacks for cards with duplicates
        // and regular individual cards for singles
        filteredCards.forEach((card, index) => {
            const cardElement = card.total_cards > 1 ? 
                createMiniFannedStack(card, index, filteredCards) : 
                createDatabaseCard(card, index, filteredCards);
            cardsGrid.appendChild(cardElement);
        });
    } else {
        // Display individual cards
        filteredCards.forEach((card, index) => {
            const cardElement = createDatabaseCard(card, index, filteredCards);
            cardsGrid.appendChild(cardElement);
        });
    }
}

// Create a mini-fanned stack for cards with duplicates in gallery view
function createMiniFannedStack(card, index, filteredCards) {
    const cardDiv = document.createElement('div');
    cardDiv.className = `card-item mini-fanned-stack color-border-${getColorBorder(card.colors)}`;
    cardDiv.onclick = () => showStackSpreadOverlay(index, filteredCards);
    
    // Create stack count badge
    const stackBadge = `<div class="stack-count-badge">${card.total_cards}</div>`;
    
    // Create example badge if it's an example card
    const exampleBadge = card.is_example ? 
        '<div class="example-badge">EXAMPLE</div>' : '';
    
    cardDiv.innerHTML = `
        <div class="card-image mini-fan-container">
            <div class="mini-fan-card mini-fan-back"></div>
            <div class="mini-fan-card mini-fan-front">
                ${card.image_url ? `<img src="${card.image_url}" alt="${card.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
            </div>
            ${stackBadge}
            ${exampleBadge}
        </div>
        <div class="card-info">
            <div class="card-name">${card.name}</div>
            <div class="card-count">Count: ${card.total_cards}</div>
        </div>
    `;
    
    return cardDiv;
}

// Show stack spread overlay (replaces the fan modal)
function showStackSpreadOverlay(index, filteredCards) {
    const card = filteredCards ? filteredCards[index] : cards[index];
    if (!card) return;
    
    currentCardIndex = index;
    
    // Create spread overlay
    const spreadOverlay = document.createElement('div');
    spreadOverlay.id = 'spreadOverlay';
    spreadOverlay.className = 'spread-overlay';
    
    // Create spread content
    const spreadContent = document.createElement('div');
    spreadContent.className = 'spread-content';
    
    // Create header
    const spreadHeader = document.createElement('div');
    spreadHeader.className = 'spread-header';
    spreadHeader.innerHTML = `
        <h3>${card.name} - Stack (${card.total_cards} cards)</h3>
        <button class="close-btn" onclick="closeSpreadOverlay()">×</button>
    `;
    
    // Create grid container
    const spreadGrid = document.createElement('div');
    spreadGrid.className = 'spread-grid';
    
    // Add cards to grid
    if (card.duplicates && card.duplicates.length > 0) {
        card.duplicates.forEach((duplicate, idx) => {
            const spreadCard = createSpreadCard(duplicate, card, idx);
            spreadGrid.appendChild(spreadCard);
        });
    } else {
        // Single card in stack
        const spreadCard = createSpreadCard(card, card, 0);
        spreadGrid.appendChild(spreadCard);
    }
    
    // Assemble overlay
    spreadContent.appendChild(spreadHeader);
    spreadContent.appendChild(spreadGrid);
    spreadOverlay.appendChild(spreadContent);
    
    // Add to document
    document.body.appendChild(spreadOverlay);
    
    // Add click outside to close
    spreadOverlay.onclick = (e) => {
        if (e.target === spreadOverlay) {
            closeSpreadOverlay();
        }
    };
    
    // Add escape key handler
    document.addEventListener('keydown', handleSpreadEscape);
}

// Create a spread card element for the grid overlay
function createSpreadCard(cardData, parentCard, index) {
    const spreadCard = document.createElement('div');
    spreadCard.className = `spread-card color-border-${getColorBorder(parentCard.colors)}`;
    
    // Add example indicator
    const exampleBadge = cardData.is_example ? '<span class="example-badge">EXAMPLE</span>' : '';
    
    spreadCard.innerHTML = `
        <div class="card-image">
            ${parentCard.image_url ? `<img src="${parentCard.image_url}" alt="${parentCard.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
            ${exampleBadge}
        </div>
        <div class="card-info">
            <div class="card-name">${parentCard.name}</div>
            <div class="card-condition">Condition: ${cardData.condition || 'Unknown'}</div>
            <div class="card-count">Count: ${cardData.count || 1}</div>
            <div class="card-added">Added: ${formatDate(cardData.first_seen)} (${formatAddedMethod(cardData.added_method)})</div>
        </div>
    `;
    
    // Add click handler to show individual card details
    spreadCard.onclick = (e) => {
        e.stopPropagation();
        showIndividualCardFromSpread(cardData, parentCard);
    };
    
    return spreadCard;
}

// Show individual card details from spread (closes spread and opens card modal)
function showIndividualCardFromSpread(cardData, parentCard) {
    // Close spread overlay
    closeSpreadOverlay();
    
    // Create a combined card object for the modal
    const combinedCard = {
        ...parentCard,
        id: cardData.id,
        count: cardData.count,
        condition: cardData.condition,
        notes: cardData.notes,
        is_example: cardData.is_example,
        first_seen: cardData.first_seen,
        last_seen: cardData.last_seen
    };
    
    // Show card details modal
    modalTitle.textContent = combinedCard.name;
    modalBody.innerHTML = createEnhancedCardDetailHTML(combinedCard, 0, 1);
    cardModal.style.display = 'block';
}

// Close spread overlay
function closeSpreadOverlay() {
    const spreadOverlay = document.getElementById('spreadOverlay');
    if (spreadOverlay) {
        document.removeEventListener('keydown', handleSpreadEscape);
        spreadOverlay.remove();
    }
}

// Handle escape key for spread overlay
function handleSpreadEscape(e) {
    if (e.key === 'Escape') {
        closeSpreadOverlay();
    }
}

// Magic color identity mapping
function getColorBorder(colors) {
    if (!colors || colors === '') return 'colorless';
    
    const colorArray = colors.split(',').map(c => c.trim().toUpperCase());
    
    if (colorArray.length === 0) return 'colorless';
    if (colorArray.length > 1) return 'multicolor';
    
    switch (colorArray[0]) {
        case 'W': return 'white';
        case 'U': return 'blue';
        case 'B': return 'black';
        case 'R': return 'red';
        case 'G': return 'green';
        default: return 'colorless';
    }
}

// Create a database card element
function createDatabaseCard(card, index, filteredCards) {
    const cardDiv = document.createElement('div');
    cardDiv.className = `card-item color-border-${getColorBorder(card.colors)}`;
    cardDiv.onclick = () => showCardDetails(index, filteredCards);
    
    // Add example indicator
    const exampleBadge = card.is_example ? '<span class="example-badge">EXAMPLE</span>' : '';
    
    // Use count from the card, default to 1 if undefined
    const cardCount = card.count || 1;
    
    cardDiv.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
            ${exampleBadge}
        </div>
        <div class="card-info">
            <div class="card-name">${card.name}</div>
            <div class="card-count">Count: ${cardCount}</div>
        </div>
    `;
    
    return cardDiv;
}



// Filter cards based on search term
function filterCards() {
    if (!searchTerm) return cards;
    
    return cards.filter(card => 
        card.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (card.set_name && card.set_name.toLowerCase().includes(searchTerm.toLowerCase()))
    );
}

// Handle search input
function handleSearch(e) {
    searchTerm = e.target.value;
    displayCards();
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/stats');
        const stats = await response.json();
        
        // Always show total stats (including examples) to give accurate count
        document.getElementById('totalCards').textContent = stats.total_unique_cards;
        document.getElementById('totalCount').textContent = stats.total_card_count;
        document.getElementById('totalValue').textContent = `$${stats.total_value_usd.toFixed(2)}`;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Show card details modal with navigation
function showCardDetails(cardIndex, filteredCards) {
    currentCardIndex = cardIndex;
    const cardsToUse = filteredCards || filterCards();
    const card = cardsToUse[cardIndex];
    
    if (!card) return;
    
    modalTitle.textContent = card.name;
    modalBody.innerHTML = createEnhancedCardDetailHTML(card, cardIndex, cardsToUse.length);
    
    // Add navigation arrows
    addNavigationArrows(cardsToUse);
    
    cardModal.style.display = 'block';
}

// Add navigation arrows to the modal
function addNavigationArrows(cardsToUse) {
    // Remove existing arrows
    const existingArrows = document.querySelectorAll('.nav-arrow');
    existingArrows.forEach(arrow => arrow.remove());
    
    const filteredCards = cardsToUse || filterCards();
    
    // Only show arrows if there are multiple cards
    if (filteredCards.length <= 1) return;
    
    // Left arrow
    if (currentCardIndex > 0) {
        const leftArrow = document.createElement('div');
        leftArrow.className = 'nav-arrow nav-arrow-left';
        leftArrow.innerHTML = '<i class="fas fa-chevron-left"></i>';
        leftArrow.onclick = () => navigateCard(-1, filteredCards);
        cardModal.appendChild(leftArrow);
    }
    
    // Right arrow
    if (currentCardIndex < filteredCards.length - 1) {
        const rightArrow = document.createElement('div');
        rightArrow.className = 'nav-arrow nav-arrow-right';
        rightArrow.innerHTML = '<i class="fas fa-chevron-right"></i>';
        rightArrow.onclick = () => navigateCard(1, filteredCards);
        cardModal.appendChild(rightArrow);
    }
}

// Navigate between cards (respects stacking toggle)
function navigateCard(direction, cardsToUse) {
    const filteredCards = cardsToUse || filterCards();
    const newIndex = currentCardIndex + direction;
    
    if (newIndex >= 0 && newIndex < filteredCards.length) {
        currentCardIndex = newIndex;
        const card = filteredCards[currentCardIndex];
        
        modalTitle.textContent = card.name;
        modalBody.innerHTML = createEnhancedCardDetailHTML(card, currentCardIndex, filteredCards.length);
        
        // Update navigation arrows
        addNavigationArrows(filteredCards);
    }
}

// Close modal
function closeModal() {
    cardModal.style.display = 'none';
}

// Show/hide loading overlay
function showLoading(show) {
    loadingOverlay.style.display = show ? 'block' : 'none';
}

// Show upload progress
function showUploadProgress() {
    uploadProgress.style.display = 'block';
}

// Hide upload progress
function hideUploadProgress() {
    uploadProgress.style.display = 'none';
}

// Update progress bar
function updateProgress(percent, text) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = text;
}

// Add test data with real Magic cards
async function addTestData() {
    // This function is called on page load to add some test data
    // In a real application, this would be removed
    console.log('Test data loaded');
}

// Update stats display
function updateStats(data) {
    const totalCardsElement = document.getElementById('totalCards');
    const totalCountElement = document.getElementById('totalCount');
    const totalValueElement = document.getElementById('totalValue');
    
    if (viewMode === 'stacked') {
        totalCardsElement.textContent = data.total_stacks || 0;
        const totalCount = cards.reduce((sum, card) => sum + (card.stack_count || 0), 0);
        totalCountElement.textContent = totalCount;
    } else {
        totalCardsElement.textContent = data.total_cards || 0;
        const totalCount = cards.reduce((sum, card) => sum + (card.count || 0), 0);
        totalCountElement.textContent = totalCount;
    }
    
    const totalValue = cards.reduce((sum, card) => sum + (card.price_usd || 0), 0);
    totalValueElement.textContent = `$${totalValue.toFixed(2)}`;
}

// Standardized grading options with user-friendly names
const CONDITION_OPTIONS = [
    { value: 'UNKNOWN', label: 'Unknown' },
    { value: 'NM', label: 'Near Mint' },
    { value: 'LP', label: 'Lightly Played' },
    { value: 'MP', label: 'Moderately Played' },
    { value: 'HP', label: 'Heavily Played' },
    { value: 'DMG', label: 'Damaged' }
];

// Standardized rarity options
const RARITY_OPTIONS = [
    { value: 'unknown', label: 'Unknown' },
    { value: 'common', label: 'Common' },
    { value: 'uncommon', label: 'Uncommon' },
    { value: 'rare', label: 'Rare' },
    { value: 'mythic', label: 'Mythic Rare' },
    { value: 'bonus', label: 'Bonus' },
    { value: 'special', label: 'Special' },
    { value: 'timeshifted', label: 'Timeshifted' },
    { value: 'masterpiece', label: 'Masterpiece' }
];

// Common Magic: The Gathering sets with their codes
const SET_OPTIONS = [
    { value: 'unknown', label: 'Unknown', code: 'UNK' },
    { value: 'lea', label: 'Limited Edition Alpha', code: 'LEA' },
    { value: 'leb', label: 'Limited Edition Beta', code: 'LEB' },
    { value: '2ed', label: 'Unlimited Edition', code: '2ED' },
    { value: 'arn', label: 'Arabian Nights', code: 'ARN' },
    { value: 'atq', label: 'Antiquities', code: 'ATQ' },
    { value: 'leg', label: 'Legends', code: 'LEG' },
    { value: 'drk', label: 'The Dark', code: 'DRK' },
    { value: 'fem', label: 'Fallen Empires', code: 'FEM' },
    { value: 'ice', label: 'Ice Age', code: 'ICE' },
    { value: 'all', label: 'Alliances', code: 'ALL' },
    { value: 'mir', label: 'Mirage', code: 'MIR' },
    { value: 'vis', label: 'Visions', code: 'VIS' },
    { value: 'wth', label: 'Weatherlight', code: 'WTH' },
    { value: 'tmp', label: 'Tempest', code: 'TMP' },
    { value: 'sth', label: 'Stronghold', code: 'STH' },
    { value: 'exo', label: 'Exodus', code: 'EXO' },
    { value: 'usg', label: 'Urza\'s Saga', code: 'USG' },
    { value: 'ulg', label: 'Urza\'s Legacy', code: 'ULG' },
    { value: 'uds', label: 'Urza\'s Destiny', code: 'UDS' },
    { value: 'mmq', label: 'Mercadian Masques', code: 'MMQ' },
    { value: 'nem', label: 'Nemesis', code: 'NEM' },
    { value: 'pcy', label: 'Prophecy', code: 'PCY' },
    { value: 'inv', label: 'Invasion', code: 'INV' },
    { value: 'pls', label: 'Planeshift', code: 'PLS' },
    { value: 'apc', label: 'Apocalypse', code: 'APC' },
    { value: 'ody', label: 'Odyssey', code: 'ODY' },
    { value: 'tor', label: 'Torment', code: 'TOR' },
    { value: 'jud', label: 'Judgment', code: 'JUD' },
    { value: 'ons', label: 'Onslaught', code: 'ONS' },
    { value: 'lgn', label: 'Legions', code: 'LGN' },
    { value: 'scg', label: 'Scourge', code: 'SCG' },
    { value: 'mrd', label: 'Mirrodin', code: 'MRD' },
    { value: 'dst', label: 'Darksteel', code: 'DST' },
    { value: '5dn', label: 'Fifth Dawn', code: '5DN' },
    { value: 'chk', label: 'Champions of Kamigawa', code: 'CHK' },
    { value: 'bok', label: 'Betrayers of Kamigawa', code: 'BOK' },
    { value: 'sok', label: 'Saviors of Kamigawa', code: 'SOK' },
    { value: 'rav', label: 'Ravnica: City of Guilds', code: 'RAV' },
    { value: 'gpt', label: 'Guildpact', code: 'GPT' },
    { value: 'dis', label: 'Dissension', code: 'DIS' },
    { value: 'tsp', label: 'Time Spiral', code: 'TSP' },
    { value: 'plc', label: 'Planar Chaos', code: 'PLC' },
    { value: 'fut', label: 'Future Sight', code: 'FUT' },
    { value: 'lrw', label: 'Lorwyn', code: 'LRW' },
    { value: 'mor', label: 'Morningtide', code: 'MOR' },
    { value: 'shm', label: 'Shadowmoor', code: 'SHM' },
    { value: 'eve', label: 'Eventide', code: 'EVE' },
    { value: 'ala', label: 'Shards of Alara', code: 'ALA' },
    { value: 'con', label: 'Conflux', code: 'CON' },
    { value: 'arb', label: 'Alara Reborn', code: 'ARB' },
    { value: 'zen', label: 'Zendikar', code: 'ZEN' },
    { value: 'wwk', label: 'Worldwake', code: 'WWK' },
    { value: 'roe', label: 'Rise of the Eldrazi', code: 'ROE' },
    { value: 'som', label: 'Scars of Mirrodin', code: 'SOM' },
    { value: 'mbs', label: 'Mirrodin Besieged', code: 'MBS' },
    { value: 'nph', label: 'New Phyrexia', code: 'NPH' },
    { value: 'isd', label: 'Innistrad', code: 'ISD' },
    { value: 'dka', label: 'Dark Ascension', code: 'DKA' },
    { value: 'avr', label: 'Avacyn Restored', code: 'AVR' },
    { value: 'rtr', label: 'Return to Ravnica', code: 'RTR' },
    { value: 'gtc', label: 'Gatecrash', code: 'GTC' },
    { value: 'dgm', label: 'Dragon\'s Maze', code: 'DGM' },
    { value: 'ths', label: 'Theros', code: 'THS' },
    { value: 'bng', label: 'Born of the Gods', code: 'BNG' },
    { value: 'jou', label: 'Journey into Nyx', code: 'JOU' },
    { value: 'ktk', label: 'Khans of Tarkir', code: 'KTK' },
    { value: 'frf', label: 'Fate Reforged', code: 'FRF' },
    { value: 'dtk', label: 'Dragons of Tarkir', code: 'DTK' },
    { value: 'bfz', label: 'Battle for Zendikar', code: 'BFZ' },
    { value: 'ogw', label: 'Oath of the Gatewatch', code: 'OGW' },
    { value: 'soi', label: 'Shadows over Innistrad', code: 'SOI' },
    { value: 'emn', label: 'Eldritch Moon', code: 'EMN' },
    { value: 'kld', label: 'Kaladesh', code: 'KLD' },
    { value: 'aer', label: 'Aether Revolt', code: 'AER' },
    { value: 'akh', label: 'Amonkhet', code: 'AKH' },
    { value: 'hou', label: 'Hour of Devastation', code: 'HOU' },
    { value: 'xln', label: 'Ixalan', code: 'XLN' },
    { value: 'rix', label: 'Rivals of Ixalan', code: 'RIX' },
    { value: 'dom', label: 'Dominaria', code: 'DOM' },
    { value: 'm19', label: 'Core Set 2019', code: 'M19' },
    { value: 'grn', label: 'Guilds of Ravnica', code: 'GRN' },
    { value: 'rna', label: 'Ravnica Allegiance', code: 'RNA' },
    { value: 'war', label: 'War of the Spark', code: 'WAR' },
    { value: 'm20', label: 'Core Set 2020', code: 'M20' },
    { value: 'eld', label: 'Throne of Eldraine', code: 'ELD' },
    { value: 'thb', label: 'Theros Beyond Death', code: 'THB' },
    { value: 'iko', label: 'Ikoria: Lair of Behemoths', code: 'IKO' },
    { value: 'm21', label: 'Core Set 2021', code: 'M21' },
    { value: 'znr', label: 'Zendikar Rising', code: 'ZNR' },
    { value: 'khm', label: 'Kaldheim', code: 'KHM' },
    { value: 'stx', label: 'Strixhaven: School of Mages', code: 'STX' },
    { value: 'afr', label: 'Adventures in the Forgotten Realms', code: 'AFR' },
    { value: 'mid', label: 'Innistrad: Midnight Hunt', code: 'MID' },
    { value: 'vow', label: 'Innistrad: Crimson Vow', code: 'VOW' },
    { value: 'neo', label: 'Kamigawa: Neon Dynasty', code: 'NEO' },
    { value: 'snc', label: 'Streets of New Capenna', code: 'SNC' },
    { value: 'dmu', label: 'Dominaria United', code: 'DMU' },
    { value: 'bro', label: 'The Brothers\' War', code: 'BRO' },
    { value: 'one', label: 'Phyrexia: All Will Be One', code: 'ONE' },
    { value: 'mom', label: 'March of the Machine', code: 'MOM' },
    { value: 'mat', label: 'March of the Machine: The Aftermath', code: 'MAT' },
    { value: 'ltr', label: 'The Lord of the Rings: Tales of Middle-earth', code: 'LTR' },
    { value: 'woe', label: 'Wilds of Eldraine', code: 'WOE' },
    { value: 'lci', label: 'The Lost Caverns of Ixalan', code: 'LCI' },
    { value: 'mkm', label: 'Murders at Karlov Manor', code: 'MKM' },
    { value: 'otj', label: 'Outlaws of Thunder Junction', code: 'OTJ' },
    { value: 'mh3', label: 'Modern Horizons 3', code: 'MH3' },
    { value: 'blb', label: 'Bloomburrow', code: 'BLB' },
    { value: 'dsk', label: 'Duskmourn: House of Horror', code: 'DSK' },
    { value: 'fdn', label: 'Foundations', code: 'FDN' },
    { value: 'bbd', label: 'Battlebond', code: 'BBD' },
    { value: 'clu', label: 'Ravnica: Clue Edition', code: 'CLU' },
    { value: 'cmr', label: 'Commander Legends', code: 'CMR' },
    { value: 'dsc', label: 'Duskmourn: House of Horror Commander', code: 'DSC' },
    { value: 'eoc', label: 'Edge of Eternities Commander', code: 'EOC' },
    { value: 'ugl', label: 'Unglued', code: 'UGL' },
    { value: 'vma', label: 'Vintage Masters', code: 'VMA' }
];

// Format date for display
function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    } catch (error) {
        return 'Unknown';
    }
}

// Format added method for display
function formatAddedMethod(method) {
    if (!method) return 'Unknown';
    
    const methodMap = {
        'SCANNED': 'Scanned',
        'MANUAL': 'Manual Entry',
        'IMPORTED': 'Imported',
        'BULK_IMPORT': 'Bulk Import',
        'LEGACY': 'Legacy Data'
    };
    
    return methodMap[method] || method;
}

// Convert mana cost string to HTML with mana symbols
function formatManaCost(manaCost) {
    if (!manaCost || manaCost === '' || manaCost === 'None') {
        return '<span class="no-mana">—</span>';
    }
    
    // Replace mana symbols with HTML spans
    let formattedCost = manaCost;
    
    // Define mana symbol mappings
    const manaSymbols = {
        '{W}': '<span class="mana-symbol mana-white"></span>',
        '{U}': '<span class="mana-symbol mana-blue"></span>',
        '{B}': '<span class="mana-symbol mana-black"></span>',
        '{R}': '<span class="mana-symbol mana-red"></span>',
        '{G}': '<span class="mana-symbol mana-green"></span>',
        '{C}': '<span class="mana-symbol mana-colorless"></span>',
        '{X}': '<span class="mana-symbol mana-generic">X</span>',
        '{Y}': '<span class="mana-symbol mana-generic">Y</span>',
        '{Z}': '<span class="mana-symbol mana-generic">Z</span>',
        
        // Generic mana costs (0-20)
        '{0}': '<span class="mana-symbol mana-generic">0</span>',
        '{1}': '<span class="mana-symbol mana-generic">1</span>',
        '{2}': '<span class="mana-symbol mana-generic">2</span>',
        '{3}': '<span class="mana-symbol mana-generic">3</span>',
        '{4}': '<span class="mana-symbol mana-generic">4</span>',
        '{5}': '<span class="mana-symbol mana-generic">5</span>',
        '{6}': '<span class="mana-symbol mana-generic">6</span>',
        '{7}': '<span class="mana-symbol mana-generic">7</span>',
        '{8}': '<span class="mana-symbol mana-generic">8</span>',
        '{9}': '<span class="mana-symbol mana-generic">9</span>',
        '{10}': '<span class="mana-symbol mana-generic">10</span>',
        '{11}': '<span class="mana-symbol mana-generic">11</span>',
        '{12}': '<span class="mana-symbol mana-generic">12</span>',
        '{13}': '<span class="mana-symbol mana-generic">13</span>',
        '{14}': '<span class="mana-symbol mana-generic">14</span>',
        '{15}': '<span class="mana-symbol mana-generic">15</span>',
        '{16}': '<span class="mana-symbol mana-generic">16</span>',
        '{17}': '<span class="mana-symbol mana-generic">17</span>',
        '{18}': '<span class="mana-symbol mana-generic">18</span>',
        '{19}': '<span class="mana-symbol mana-generic">19</span>',
        '{20}': '<span class="mana-symbol mana-generic">20</span>',
        
        // Hybrid mana
        '{W/U}': '<span class="mana-symbol mana-hybrid mana-wu">W/U</span>',
        '{W/B}': '<span class="mana-symbol mana-hybrid mana-wb">W/B</span>',
        '{U/B}': '<span class="mana-symbol mana-hybrid mana-ub">U/B</span>',
        '{U/R}': '<span class="mana-symbol mana-hybrid mana-ur">U/R</span>',
        '{B/R}': '<span class="mana-symbol mana-hybrid mana-br">B/R</span>',
        '{B/G}': '<span class="mana-symbol mana-hybrid mana-bg">B/G</span>',
        '{R/G}': '<span class="mana-symbol mana-hybrid mana-rg">R/G</span>',
        '{R/W}': '<span class="mana-symbol mana-hybrid mana-rw">R/W</span>',
        '{G/W}': '<span class="mana-symbol mana-hybrid mana-gw">G/W</span>',
        '{G/U}': '<span class="mana-symbol mana-hybrid mana-gu">G/U</span>',
        
        // Phyrexian mana
        '{W/P}': '<span class="mana-symbol mana-phyrexian mana-wp">W/P</span>',
        '{U/P}': '<span class="mana-symbol mana-phyrexian mana-up">U/P</span>',
        '{B/P}': '<span class="mana-symbol mana-phyrexian mana-bp">B/P</span>',
        '{R/P}': '<span class="mana-symbol mana-phyrexian mana-rp">R/P</span>',
        '{G/P}': '<span class="mana-symbol mana-phyrexian mana-gp">G/P</span>',
        
        // Snow mana
        '{S}': '<span class="mana-symbol mana-snow"></span>',
        
        // Tap symbol
        '{T}': '<span class="mana-symbol mana-tap"></span>',
        
        // Energy
        '{E}': '<span class="mana-symbol mana-energy"></span>'
    };
    
    // Replace each mana symbol
    for (const [symbol, html] of Object.entries(manaSymbols)) {
        formattedCost = formattedCost.replace(new RegExp(symbol.replace(/[{}]/g, '\\$&'), 'g'), html);
    }
    
    return formattedCost;
}

// Create enhanced card detail HTML with navigation
function createEnhancedCardDetailHTML(card, index, total) {
    const condition = card.condition && CONDITION_OPTIONS.find(opt => opt.value === card.condition) ? card.condition : 'LP';
    const conditionDropdown = card.id && card.id !== 'undefined' ? `
        <select id="conditionDropdown" onchange="updateCardCondition(${card.id}, this.value)">
            ${CONDITION_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === condition ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    ` : `
        <select id="conditionDropdown" disabled>
            ${CONDITION_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === condition ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    `;
    
    const rarity = card.rarity && RARITY_OPTIONS.find(opt => opt.value === card.rarity.toLowerCase()) ? card.rarity.toLowerCase() : 'unknown';
    const rarityDropdown = card.id && card.id !== 'undefined' ? `
        <select id="rarityDropdown" onchange="updateCardRarity(${card.id}, this.value)">
            ${RARITY_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === rarity ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    ` : `
        <select id="rarityDropdown" disabled>
            ${RARITY_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === rarity ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    `;
    
    const setCode = card.set_code ? card.set_code.toLowerCase() : 'unknown';
    const setDropdown = card.id && card.id !== 'undefined' ? `
        <select id="setDropdown" onchange="updateCardSet(${card.id}, this.value)">
            ${SET_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === setCode ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    ` : `
        <select id="setDropdown" disabled>
            ${SET_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === setCode ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    `;
    
    return `
        <div class="card-detail-container">
            <div class="card-image-section">
                <img src="${card.image_url || 'https://via.placeholder.com/300x420/667eea/ffffff?text=Card+Image'}" 
                     alt="${card.name}" 
                     class="card-image-large"
                     onerror="this.src='https://via.placeholder.com/300x420/667eea/ffffff?text=Card+Image'">
                ${card.is_example ? '<div class="example-badge">EXAMPLE</div>' : ''}
            </div>
            <div class="card-details">
                <div class="detail-row">
                    <span class="detail-label">Name:</span>
                    <span class="detail-value">${card.name}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Set:</span>
                    <span class="detail-value">${setDropdown}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Rarity:</span>
                    <span class="detail-value">${rarityDropdown}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Mana Cost:</span>
                    <span class="detail-value mana-cost-display">${formatManaCost(card.mana_cost)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Count:</span>
                    <span class="detail-value">${card.count || 1}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Condition:</span>
                    <span class="detail-value">${conditionDropdown}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Added:</span>
                    <span class="detail-value">
                        ${formatDate(card.first_seen)} 
                        <span class="added-method">(${formatAddedMethod(card.added_method)})</span>
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Prices:</span>
                    <div class="price-details">
                        <span class="price-item price-usd">$${(card.price_usd || 0).toFixed(2)}</span>
                        <span class="price-item price-eur">€${(card.price_eur || 0).toFixed(2)}</span>
                    </div>
                </div>
                ${card.oracle_text ? `
                <div class="detail-row">
                    <span class="detail-label">Oracle Text:</span>
                    <div class="oracle-text">${card.oracle_text}</div>
                </div>
                ` : ''}
                <div class="card-actions">
                    ${card.id && card.id !== 'undefined' ? `
                        <button class="action-btn" onclick="editCard(${card.id})">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="action-btn delete-btn" onclick="deleteCard(${card.id})">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    ` : `
                        <button class="action-btn disabled" disabled>
                            <i class="fas fa-edit"></i> Edit (No ID)
                        </button>
                        <button class="action-btn delete-btn disabled" disabled>
                            <i class="fas fa-trash"></i> Delete (No ID)
                        </button>
                    `}
                </div>
            </div>
        </div>
        <div class="nav-controls">
            <button class="nav-btn" onclick="navigateCard(-1)" ${index === 0 ? 'disabled' : ''}>
                <i class="fas fa-chevron-left"></i> Previous
            </button>
            <span class="card-counter">${index + 1} of ${total}</span>
            <button class="nav-btn" onclick="navigateCard(1)" ${index === total - 1 ? 'disabled' : ''}>
                Next <i class="fas fa-chevron-right"></i>
            </button>
        </div>
    `;
}

// Update card condition via API
async function updateCardCondition(cardId, newCondition) {
    // Validate card ID
    if (!cardId || cardId === 'undefined' || cardId === undefined) {
        alert('Cannot update card: Invalid card ID');
        console.error('Attempted to update card condition with invalid ID:', cardId);
        return;
    }
    
    try {
        const response = await fetch(`/cards/${cardId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ condition: newCondition })
        });
        if (response.ok) {
            await loadCards();
        } else {
            alert('Failed to update card condition.');
        }
    } catch (error) {
        console.error('Error updating card condition:', error);
        alert('Error updating card condition.');
    }
}

// Update card rarity via API
async function updateCardRarity(cardId, newRarity) {
    // Validate card ID
    if (!cardId || cardId === 'undefined' || cardId === undefined) {
        alert('Cannot update card: Invalid card ID');
        console.error('Attempted to update card rarity with invalid ID:', cardId);
        return;
    }
    
    try {
        const response = await fetch(`/cards/${cardId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rarity: newRarity })
        });
        if (response.ok) {
            await loadCards();
        } else {
            alert('Failed to update card rarity.');
        }
    } catch (error) {
        console.error('Error updating card rarity:', error);
        alert('Error updating card rarity.');
    }
}

// Update card set and automatically update set code
async function updateCardSet(cardId, newSetValue) {
    // Validate card ID
    if (!cardId || cardId === 'undefined' || cardId === undefined) {
        alert('Cannot update card: Invalid card ID');
        console.error('Attempted to update card set with invalid ID:', cardId);
        return;
    }
    
    try {
        const selectedSet = SET_OPTIONS.find(opt => opt.value === newSetValue);
        const setCode = selectedSet ? selectedSet.code : 'UNK';
        const setName = selectedSet ? selectedSet.label : 'Unknown';
        
        // Update the set code display immediately
        const setCodeDisplay = document.getElementById('setCodeDisplay');
        if (setCodeDisplay) {
            setCodeDisplay.textContent = setCode;
        }
        
        const response = await fetch(`/cards/${cardId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                set_code: setCode,
                set_name: setName
            })
        });
        if (response.ok) {
            await loadCards();
        } else {
            alert('Failed to update card set.');
        }
    } catch (error) {
        console.error('Error updating card set:', error);
        alert('Error updating card set.');
    }
}

// Edit card details
async function editCard(cardId) {
    // Validate card ID
    if (!cardId || cardId === 'undefined' || cardId === undefined) {
        alert('Cannot edit card: Invalid card ID');
        console.error('Attempted to edit card with invalid ID:', cardId);
        return;
    }
    
    // This would open an edit modal - for now, just show an alert
    alert('Edit functionality coming soon!');
}

// Delete card
async function deleteCard(cardId) {
    // Validate card ID
    if (!cardId || cardId === 'undefined' || cardId === undefined) {
        alert('Cannot delete card: Invalid card ID');
        console.error('Attempted to delete card with invalid ID:', cardId);
        return;
    }
    
    if (!confirm('Are you sure you want to delete this card?')) {
        return;
    }
    
    try {
        const response = await fetch(`/cards/${cardId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await loadCards();
            await loadStats();
            closeModal();
        } else {
            let errorMessage = 'Error deleting card';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorMessage;
            } catch (e) {
                // Use default error message if parsing fails
            }
            alert(errorMessage);
        }
    } catch (error) {
        console.error('Error deleting card:', error);
        alert('Error deleting card: ' + error.message);
    }
}

// Add some CSS for card details
const style = document.createElement('style');
style.textContent = `
    .card-detail {
        line-height: 1.6;
    }
    .detail-row {
        margin-bottom: 15px;
    }
    .price-details {
        display: flex;
        gap: 15px;
        margin-top: 5px;
    }
    .oracle-text {
        background: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-top: 5px;
        font-style: italic;
        white-space: pre-wrap;
    }
    .action-btn.disabled {
        opacity: 0.5;
        cursor: not-allowed;
        background-color: #e9ecef;
        color: #6c757d;
    }
    .action-btn.disabled:hover {
        background-color: #e9ecef;
        transform: none;
    }
    select:disabled {
        background-color: #e9ecef;
        color: #6c757d;
        cursor: not-allowed;
    }
`;
document.head.appendChild(style);

// ===== SCANNING MODAL FUNCTIONALITY =====

// Global scanning variables
// Show scanning modal and start workflow
async function showScanningModal(scanId, uploadedFiles) {
    currentScan = {
        id: scanId,
        files: uploadedFiles,
        results: [],
        phase: 'processing'
    };
    
    const modal = document.getElementById('scanningModal');
    const title = document.getElementById('scanningTitle');
    const body = document.getElementById('scanningBody');
    
    title.textContent = 'Scanning Magic Cards';
    modal.style.display = 'block';
    
    // Show processing phase
    showProcessingPhase();
    
    // Add small delay to ensure upload has completed
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // Start processing the scan with retry logic
    try {
        await startScanProcessingWithRetry(scanId);
        // Start polling for updates
        startScanPolling(scanId);
    } catch (error) {
        console.error('Error starting scan processing:', error);
        showScanError('Failed to start processing. Please try again.');
    }
}

// Show processing phase
function showProcessingPhase() {
    const body = document.getElementById('scanningBody');
    
    body.innerHTML = `
        <div class="scanning-phase">
            <div class="scan-phase-indicator">
                <div class="scan-phase-step completed">
                    <div class="scan-phase-circle">1</div>
                    <div class="scan-phase-label">Upload</div>
                </div>
                <div class="scan-phase-step active">
                    <div class="scan-phase-circle">2</div>
                    <div class="scan-phase-label">Processing</div>
                </div>
                <div class="scan-phase-step">
                    <div class="scan-phase-circle">3</div>
                    <div class="scan-phase-label">Review</div>
                </div>
                <div class="scan-phase-step">
                    <div class="scan-phase-circle">4</div>
                    <div class="scan-phase-label">Complete</div>
                </div>
            </div>
            
            <h3>
                <span class="scan-spinner"></span>
                Processing Images...
            </h3>
            <p>AI is identifying Magic cards in your uploaded images.</p>
            
            <div class="scanning-images" id="scanningImages">
                ${currentScan.files.map((file, index) => `
                    <div class="scan-image-item processing" id="scanImage${index}">
                        <img src="${URL.createObjectURL(file)}" alt="${file.name}" class="scan-image-full">
                        <div class="scan-image-status processing">Processing...</div>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="scan-controls">
            <div class="scan-summary">
                Processing ${currentScan.files.length} image${currentScan.files.length > 1 ? 's' : ''}...
                <div class="scan-status-note">You can cancel at any time</div>
            </div>
            <button class="scan-secondary-btn" onclick="cancelScan()" id="cancelScanBtn">
                <i class="fas fa-times"></i> Cancel Scan
            </button>
        </div>
    `;
}

// Start scan processing with retry logic
async function startScanProcessingWithRetry(scanId, maxRetries = 3) {
    console.log(`Starting scan processing for scan ID: ${scanId}`);
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            console.log(`Processing attempt ${attempt}/${maxRetries}`);
            const response = await fetch(`/scan/${scanId}/process`, {
                method: 'POST'
            });
            
            if (!response.ok) {
                let errorMessage = 'Failed to start processing';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorData.error || errorMessage;
                } catch (e) {
                    const errorText = await response.text();
                    errorMessage = errorText || errorMessage;
                }
                
                console.error(`Processing attempt ${attempt} failed:`, response.status, errorMessage);
                
                // If it's a 400 error (scan not ready), retry after delay
                if (response.status === 400 && attempt < maxRetries) {
                    console.log(`Scan not ready, retrying in ${attempt * 500}ms (attempt ${attempt}/${maxRetries})`);
                    await new Promise(resolve => setTimeout(resolve, attempt * 500));
                    continue;
                }
                
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            console.log(`Processing started successfully:`, result);
            return result;
        } catch (error) {
            console.error(`Processing attempt ${attempt} error:`, error);
            if (attempt === maxRetries) {
                console.error('Error starting scan processing after retries:', error);
                throw error;
            }
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, attempt * 500));
        }
    }
}

// Start scan processing
async function startScanProcessing(scanId) {
    try {
        const response = await fetch(`/scan/${scanId}/process`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            let errorMessage = 'Failed to start processing';
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorMessage;
            } catch (e) {
                const errorText = await response.text();
                errorMessage = errorText || errorMessage;
            }
            throw new Error(errorMessage);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Error starting scan processing:', error);
        throw error;
    }
}

// Start polling for scan status
function startScanPolling(scanId) {
    // Clear any existing polling
    if (scanPollingInterval) {
        clearInterval(scanPollingInterval);
    }
    
    scanPollingInterval = setInterval(async () => {
        try {
            await updateScanStatus(scanId);
        } catch (error) {
            console.error('Error polling scan status:', error);
        }
    }, 2000); // Poll every 2 seconds
}

// Update scan status
async function updateScanStatus(scanId) {
    try {
        const response = await fetch(`/scan/${scanId}/status`);
        
        if (!response.ok) {
            throw new Error('Failed to get scan status');
        }
        
        const status = await response.json();
        
        // Update UI based on status
        if (status.status === 'READY_FOR_REVIEW') {
            clearInterval(scanPollingInterval);
            await showReviewPhase(scanId);
        } else if (status.status === 'FAILED') {
            clearInterval(scanPollingInterval);
            showScanError('Scan failed. Please try again.');
        } else if (status.status === 'COMPLETED') {
            clearInterval(scanPollingInterval);
            showScanError('Scan was completed by another process.');
        }
        
        // Update processing progress if still processing
        updateProcessingProgress(status);
        
    } catch (error) {
        console.error('Error updating scan status:', error);
    }
}

// Update processing progress
function updateProcessingProgress(status) {
    if (status.processed_images > 0) {
        // Mark processed images as completed
        for (let i = 0; i < status.processed_images; i++) {
            const imageElement = document.getElementById(`scanImage${i}`);
            if (imageElement) {
                imageElement.className = 'scan-image-item completed';
                imageElement.querySelector('.scan-image-status').textContent = 'Completed';
                imageElement.querySelector('.scan-image-status').className = 'scan-image-status completed';
            }
        }
    }
}

// Show review phase
async function showReviewPhase(scanId) {
    try {
        // Get scan results
        const response = await fetch(`/scan/${scanId}/results`);
        
        if (!response.ok) {
            throw new Error('Failed to get scan results');
        }
        
        const resultsData = await response.json();
        currentScan.results = resultsData.results;
        currentScan.phase = 'review';
        
        // Update modal UI
        showReviewInterface(resultsData.results);
        
    } catch (error) {
        console.error('Error showing review phase:', error);
        showScanError('Failed to load scan results.');
    }
}

// Show review interface
function showReviewInterface(results) {
    const body = document.getElementById('scanningBody');
    const title = document.getElementById('scanningTitle');
    
    title.textContent = 'Review Identified Cards';
    
    // Handle case when no cards are found
    if (results.length === 0) {
        body.innerHTML = `
            <div class="scanning-phase">
                <div class="scan-phase-indicator">
                    <div class="scan-phase-step completed">
                        <div class="scan-phase-circle">1</div>
                        <div class="scan-phase-label">Upload</div>
                    </div>
                    <div class="scan-phase-step completed">
                        <div class="scan-phase-circle">2</div>
                        <div class="scan-phase-label">Processing</div>
                    </div>
                    <div class="scan-phase-step active">
                        <div class="scan-phase-circle">3</div>
                        <div class="scan-phase-label">Review</div>
                    </div>
                    <div class="scan-phase-step">
                        <div class="scan-phase-circle">4</div>
                        <div class="scan-phase-label">Complete</div>
                    </div>
                </div>
                
                <div class="no-cards-found">
                    <h3>No Cards Found</h3>
                    <p>The AI couldn't identify any Magic cards in your uploaded images.</p>
                    
                    <div class="scan-images-preview">
                        <h4>Scanned Images:</h4>
                        <div class="scanned-images-grid">
                            ${currentScan.files.map((file, index) => `
                                <div class="scanned-image-item">
                                    <img src="${URL.createObjectURL(file)}" alt="Scanned image ${index + 1}" 
                                         class="scanned-image-preview clickable-image"
                                         onclick="showFullScanImage('${file.name}', '${URL.createObjectURL(file)}')">
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="scan-controls">
                <div class="scan-summary">
                    No cards found in ${currentScan.files.length} image${currentScan.files.length > 1 ? 's' : ''}
                </div>
                <div class="scan-action-buttons">
                    <button class="scan-secondary-btn" onclick="cancelScan()">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                    <button class="scan-primary-btn" onclick="finishScan()">
                        <i class="fas fa-arrow-right"></i> Continue
                    </button>
                </div>
            </div>
        `;
        return;
    }
    
    // Normal review interface for when cards are found
    body.innerHTML = `
        <div class="scanning-phase">
            <div class="scan-phase-indicator">
                <div class="scan-phase-step completed">
                    <div class="scan-phase-circle">1</div>
                    <div class="scan-phase-label">Upload</div>
                </div>
                <div class="scan-phase-step completed">
                    <div class="scan-phase-circle">2</div>
                    <div class="scan-phase-label">Processing</div>
                </div>
                <div class="scan-phase-step active">
                    <div class="scan-phase-circle">3</div>
                    <div class="scan-phase-label">Review</div>
                </div>
                <div class="scan-phase-step">
                    <div class="scan-phase-circle">4</div>
                    <div class="scan-phase-label">Complete</div>
                </div>
            </div>
            
            <div class="scan-review-header">
                <h3>Review Identified Cards (${results.length})</h3>
                <p>Accept or reject each identified card before adding to your collection.</p>
                
                <div class="scan-bulk-actions">
                    <button class="scan-secondary-btn" onclick="acceptAllResults()">
                        <i class="fas fa-check-circle"></i> Accept All
                    </button>
                    <button class="scan-secondary-btn" onclick="rejectAllResults()">
                        <i class="fas fa-times-circle"></i> Reject All
                    </button>
                </div>
            </div>
            
            <div class="scan-results-container">
                <div class="scan-results" id="scanResults">
                    ${results.map(result => createScanResultItem(result)).join('')}
                </div>
            </div>
        </div>
        
        <div class="scan-controls">
            <div class="scan-summary">
                ${results.filter(r => r.status === 'ACCEPTED').length} accepted, 
                ${results.filter(r => r.status === 'REJECTED').length} rejected of ${results.length} cards
            </div>
            <div class="scan-action-buttons">
                <button class="scan-secondary-btn" onclick="cancelScan()">
                    <i class="fas fa-times"></i> Cancel
                </button>
                <button class="scan-primary-btn" onclick="commitAcceptedCards()" id="commitButton">
                    <i class="fas fa-plus"></i> Add Accepted to Collection
                </button>
            </div>
        </div>
    `;
    
    // Update the commit button state
    updateCommitButtonState();
}

// Create scan result item HTML
function createScanResultItem(result) {
    const confidenceClass = getConfidenceClass(result.confidence_score);
    const isAccepted = result.status === 'ACCEPTED';
    const isRejected = result.status === 'REJECTED';
    
    // Extract official image URL from card data
    let officialImageUrl = null;
    let imageUrl = 'https://via.placeholder.com/60x84/667eea/ffffff?text=No+Image';
    
    // Try to get official card image from card data with better parsing
    if (result.card_data) {
        // Handle direct image_url property
        if (result.card_data.image_url) {
            officialImageUrl = result.card_data.image_url;
            imageUrl = result.card_data.image_url;
        }
        // Handle Scryfall image_uris format
        else if (result.card_data.image_uris) {
            if (result.card_data.image_uris.normal) {
                officialImageUrl = result.card_data.image_uris.normal;
                imageUrl = result.card_data.image_uris.normal;
            } else if (result.card_data.image_uris.large) {
                officialImageUrl = result.card_data.image_uris.large;
                imageUrl = result.card_data.image_uris.large;
            } else if (result.card_data.image_uris.small) {
                officialImageUrl = result.card_data.image_uris.small;
                imageUrl = result.card_data.image_uris.small;
            }
        }
    }
    
    // If no official image found, use scan image for display and placeholder for comparison
    if (!officialImageUrl) {
        if (result.image_filename) {
            imageUrl = `/uploads/${result.image_filename}`;
        }
        officialImageUrl = 'https://via.placeholder.com/250x349/667eea/ffffff?text=No+Official+Image+Available';
    }
    
    // Create clickable image with comparison functionality
    const imageClickHandler = `showImageComparison('${result.card_name}', '${officialImageUrl}', '${result.image_filename ? `/uploads/${result.image_filename}` : ''}')`;
    
    return `
        <div class="scan-result-item ${isAccepted ? 'accepted' : ''} ${isRejected ? 'rejected' : ''}" data-result-id="${result.id}">
            <div class="scan-result-image-container">
                <img src="${imageUrl}" alt="${result.card_name}" class="scan-result-image clickable-image" 
                     onclick="${imageClickHandler}"
                     onerror="this.src='https://via.placeholder.com/60x84/667eea/ffffff?text=No+Image'">
                ${isAccepted ? '<div class="scan-result-overlay accepted"><i class="fas fa-check"></i></div>' : ''}
                ${isRejected ? '<div class="scan-result-overlay rejected"><i class="fas fa-times"></i></div>' : ''}
            </div>
            <div class="scan-result-info">
                <div class="scan-result-name">${result.card_name}</div>
                <div class="scan-result-set">${result.set_name || 'Unknown Set'}</div>
                <div class="scan-result-confidence">
                    <span class="confidence-score ${confidenceClass}">
                        ${Math.round(result.confidence_score)}% confidence
                    </span>
                    ${result.requires_review ? '<span class="review-warning">⚠ Needs review</span>' : ''}
                </div>
            </div>
            <div class="scan-result-actions">
                <button class="scan-action-btn accept ${isAccepted ? 'active' : ''}" 
                        onclick="acceptResult(${result.id})" 
                        data-result-id="${result.id}">
                    <i class="fas fa-check"></i> ${isAccepted ? 'Accepted' : 'Accept'}
                </button>
                <button class="scan-action-btn reject ${isRejected ? 'active' : ''}" 
                        onclick="rejectResult(${result.id})" 
                        data-result-id="${result.id}">
                    <i class="fas fa-times"></i> ${isRejected ? 'Rejected' : 'Reject'}
                </button>
            </div>
        </div>
    `;
}

// Get confidence class for styling
function getConfidenceClass(score) {
    if (score >= 90) return 'confidence-very-high';
    if (score >= 70) return 'confidence-high';
    if (score >= 50) return 'confidence-medium';
    if (score >= 30) return 'confidence-low';
    return 'confidence-very-low';
}

// Accept a specific result
async function acceptResult(resultId) {
    try {
        await updateResultStatus(resultId, 'accept');
        updateResultUI(resultId, 'accepted');
    } catch (error) {
        console.error('Error accepting result:', error);
    }
}

// Reject a specific result
async function rejectResult(resultId) {
    try {
        await updateResultStatus(resultId, 'reject');
        updateResultUI(resultId, 'rejected');
    } catch (error) {
        console.error('Error rejecting result:', error);
    }
}

// Update result status via API
async function updateResultStatus(resultId, action) {
    const endpoint = action === 'accept' ? 'accept' : 'reject';
    
    const response = await fetch(`/scan/${currentScan.id}/${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            result_ids: [resultId]
        })
    });
    
    if (!response.ok) {
        throw new Error(`Failed to ${action} result`);
    }
}

// Update result UI
function updateResultUI(resultId, status) {
    const resultElement = document.querySelector(`[data-result-id="${resultId}"]`);
    if (resultElement) {
        // Update main container classes
        resultElement.className = `scan-result-item ${status}`;
        
        // Update image overlay
        const imageContainer = resultElement.querySelector('.scan-result-image-container');
        const existingOverlay = imageContainer.querySelector('.scan-result-overlay');
        if (existingOverlay) {
            existingOverlay.remove();
        }
        
        if (status === 'accepted') {
            imageContainer.insertAdjacentHTML('beforeend', '<div class="scan-result-overlay accepted"><i class="fas fa-check"></i></div>');
        } else if (status === 'rejected') {
            imageContainer.insertAdjacentHTML('beforeend', '<div class="scan-result-overlay rejected"><i class="fas fa-times"></i></div>');
        }
        
        // Update buttons
        const acceptBtn = resultElement.querySelector('.accept');
        const rejectBtn = resultElement.querySelector('.reject');
        
        if (status === 'accepted') {
            acceptBtn.innerHTML = '<i class="fas fa-check"></i> Accepted';
            acceptBtn.className = 'scan-action-btn accept active';
            rejectBtn.innerHTML = '<i class="fas fa-times"></i> Reject';
            rejectBtn.className = 'scan-action-btn reject';
        } else if (status === 'rejected') {
            rejectBtn.innerHTML = '<i class="fas fa-times"></i> Rejected';
            rejectBtn.className = 'scan-action-btn reject active';
            acceptBtn.innerHTML = '<i class="fas fa-check"></i> Accept';
            acceptBtn.className = 'scan-action-btn accept';
        } else {
            // Reset to pending state
            acceptBtn.innerHTML = '<i class="fas fa-check"></i> Accept';
            acceptBtn.className = 'scan-action-btn accept';
            rejectBtn.innerHTML = '<i class="fas fa-times"></i> Reject';
            rejectBtn.className = 'scan-action-btn reject';
        }
        
        // Update the scan result status in our local data
        if (currentScan && currentScan.results) {
            const result = currentScan.results.find(r => r.id === resultId);
            if (result) {
                result.status = status.toUpperCase();
            }
        }
        
        // Update summary and commit button
        updateScanSummary();
        updateCommitButtonState();
    }
}

// Accept all results
async function acceptAllResults() {
    try {
        const response = await fetch(`/scan/${currentScan.id}/accept`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                accept_all: true
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to accept all results');
        }
        
        // Update all result UIs
        currentScan.results.forEach(result => {
            updateResultUI(result.id, 'accepted');
        });
        
        console.log('All results accepted successfully');
        
    } catch (error) {
        console.error('Error accepting all results:', error);
        alert('Failed to accept all results. Please try again.');
    }
}

// Reject all results
async function rejectAllResults() {
    try {
        const resultIds = currentScan.results.map(result => result.id);
        
        const response = await fetch(`/scan/${currentScan.id}/reject`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                result_ids: resultIds
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to reject all results');
        }
        
        // Update all result UIs
        currentScan.results.forEach(result => {
            updateResultUI(result.id, 'rejected');
        });
        
        console.log('All results rejected successfully');
        
    } catch (error) {
        console.error('Error rejecting all results:', error);
        alert('Failed to reject all results. Please try again.');
    }
}

// Update scan summary display
function updateScanSummary() {
    const summaryElement = document.querySelector('.scan-summary');
    if (summaryElement && currentScan && currentScan.results) {
        const accepted = currentScan.results.filter(r => r.status === 'ACCEPTED').length;
        const rejected = currentScan.results.filter(r => r.status === 'REJECTED').length;
        const total = currentScan.results.length;
        
        summaryElement.textContent = `${accepted} accepted, ${rejected} rejected of ${total} cards`;
    }
}

// Update commit button state
function updateCommitButtonState() {
    const commitButton = document.getElementById('commitButton');
    if (commitButton && currentScan && currentScan.results) {
        const acceptedCount = currentScan.results.filter(r => r.status === 'ACCEPTED').length;
        
        if (acceptedCount > 0) {
            commitButton.disabled = false;
            commitButton.innerHTML = `<i class="fas fa-plus"></i> Add ${acceptedCount} Card${acceptedCount !== 1 ? 's' : ''} to Collection`;
            commitButton.className = 'scan-primary-btn';
        } else {
            commitButton.disabled = true;
            commitButton.innerHTML = '<i class="fas fa-plus"></i> No Cards to Add';
            commitButton.className = 'scan-primary-btn disabled';
        }
    }
}

// Commit accepted cards to collection
async function commitAcceptedCards() {
    if (!currentScan || !currentScan.id) {
        alert('No active scan to commit');
        return;
    }
    
    const acceptedCount = currentScan.results.filter(r => r.status === 'ACCEPTED').length;
    if (acceptedCount === 0) {
        alert('No cards have been accepted. Please accept at least one card before committing.');
        return;
    }
    
    // Show loading state
    const commitButton = document.getElementById('commitButton');
    const originalText = commitButton.innerHTML;
    commitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding to Collection...';
    commitButton.disabled = true;
    
    try {
        const response = await fetch(`/scan/${currentScan.id}/commit`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.text();
            throw new Error(`Failed to commit scan: ${errorData}`);
        }
        
        const result = await response.json();
        console.log('Scan committed successfully:', result);
        
        // Show success and close modal
        showScanSuccess(result.cards_created);
        
    } catch (error) {
        console.error('Error committing scan:', error);
        alert(`Failed to add cards to collection: ${error.message}`);
        
        // Restore button state
        commitButton.innerHTML = originalText;
        commitButton.disabled = false;
    }
}

// Commit scan and add accepted cards to collection
async function commitScan() {
    try {
        const response = await fetch(`/scan/${currentScan.id}/commit`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Failed to commit scan');
        }
        
        const result = await response.json();
        
        // Show success and close modal
        showScanSuccess(result.cards_created);
        
    } catch (error) {
        console.error('Error committing scan:', error);
        showScanError('Failed to add cards to collection.');
    }
}

// Show scan success
function showScanSuccess(cardsCreated) {
    const body = document.getElementById('scanningBody');
    const title = document.getElementById('scanningTitle');
    
    title.textContent = 'Scan Complete!';
    
    body.innerHTML = `
        <div class="scanning-phase">
            <div class="scan-phase-indicator">
                <div class="scan-phase-step completed">
                    <div class="scan-phase-circle">1</div>
                    <div class="scan-phase-label">Upload</div>
                </div>
                <div class="scan-phase-step completed">
                    <div class="scan-phase-circle">2</div>
                    <div class="scan-phase-label">Processing</div>
                </div>
                <div class="scan-phase-step completed">
                    <div class="scan-phase-circle">3</div>
                    <div class="scan-phase-label">Review</div>
                </div>
                <div class="scan-phase-step completed">
                    <div class="scan-phase-circle">4</div>
                    <div class="scan-phase-label">Complete</div>
                </div>
            </div>
            
            <div style="text-align: center; padding: 40px;">
                <i class="fas fa-check-circle" style="font-size: 4rem; color: #28a745; margin-bottom: 20px;"></i>
                <h3>Successfully Added ${cardsCreated} Card${cardsCreated !== 1 ? 's' : ''}</h3>
                <p>Your cards have been added to your collection!</p>
            </div>
        </div>
        
        <div class="scan-controls">
            <div></div>
            <div></div>
            <button class="scan-primary-btn" onclick="finishScan()">
                Continue
            </button>
        </div>
    `;
}

// Show scan error
function showScanError(message) {
    const body = document.getElementById('scanningBody');
    
    body.innerHTML = `
        <div class="scanning-phase">
            <div style="text-align: center; padding: 40px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 4rem; color: #dc3545; margin-bottom: 20px;"></i>
                <h3>Scan Error</h3>
                <p>${message}</p>
            </div>
        </div>
        
        <div class="scan-controls">
            <div></div>
            <div></div>
            <button class="scan-secondary-btn" onclick="closeScanningModal()">
                Close
            </button>
        </div>
    `;
}

// Finish scan and refresh main view
async function finishScan() {
    closeScanningModal();
    
    // Refresh the main card gallery
    await loadCards();
    await loadStats();
}

// Cancel scan
async function cancelScan() {
    if (confirm('Are you sure you want to cancel this scan?')) {
        try {
            // Stop any ongoing polling immediately
            if (scanPollingInterval) {
                clearInterval(scanPollingInterval);
                scanPollingInterval = null;
            }
            
            // Update UI to show cancellation in progress
            const scanBody = document.getElementById('scanningBody');
            if (scanBody) {
                scanBody.innerHTML = `
                    <div class="scanning-phase">
                        <div style="text-align: center; padding: 40px;">
                            <i class="fas fa-spinner fa-spin" style="font-size: 2rem; color: #667eea; margin-bottom: 20px;"></i>
                            <h3>Cancelling scan...</h3>
                            <p>Please wait while we cancel the scan and clean up files.</p>
                        </div>
                    </div>
                `;
            }
            
            // Send cancellation request to backend
            if (currentScan && currentScan.id) {
                const response = await fetch(`/scan/${currentScan.id}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    console.log('Scan cancelled successfully');
                } else {
                    console.warn('Scan cancellation request failed, but proceeding with cleanup');
                }
            }
            
            // Close the modal and clean up
            closeScanningModal();
            
        } catch (error) {
            console.error('Error cancelling scan:', error);
            // Even if cancellation fails, close the modal
            closeScanningModal();
        }
    }
}

// Close scanning modal
function closeScanningModal() {
    const modal = document.getElementById('scanningModal');
    modal.style.display = 'none';
    
    // Clear polling
    if (scanPollingInterval) {
        clearInterval(scanPollingInterval);
        scanPollingInterval = null;
    }
    
    // Clean up object URLs
    if (currentScan && currentScan.files) {
        currentScan.files.forEach(file => {
            URL.revokeObjectURL(URL.createObjectURL(file));
        });
    }
    
    currentScan = null;
}

// Show image comparison dialog
function showImageComparison(cardName, officialImageUrl, scanImageUrl) {
    // Create comparison modal
    const comparisonModal = document.createElement('div');
    comparisonModal.id = 'imageComparisonModal';
    comparisonModal.className = 'image-comparison-modal';
    
    const modalContent = `
        <div class="image-comparison-content">
            <div class="image-comparison-header">
                <h3>${cardName}</h3>
                <button class="close-btn" onclick="closeImageComparison()">&times;</button>
            </div>
            <div class="image-comparison-body">
                <div class="comparison-column left-column">
                    <h4>Official Image</h4>
                    <div class="official-image-container">
                        <img src="${officialImageUrl}" alt="${cardName} - Official" class="official-comparison-image"
                             onerror="this.src='https://via.placeholder.com/250x349/667eea/ffffff?text=No+Official+Image+Found'; this.parentNode.innerHTML='<div class=&quot;no-official-image&quot;><i class=&quot;fas fa-image&quot;></i><p>No official image available</p><p>This card may not be in the Scryfall database</p></div>';">
                    </div>
                </div>
                <div class="comparison-column right-column">
                    <h4>Scanned Image</h4>
                    <div class="scan-image-container">
                        ${scanImageUrl ? `
                            <div class="zoomable-image-container">
                                <img src="${scanImageUrl}" alt="${cardName} - Scan" class="scan-comparison-image"
                                     onerror="this.src='https://via.placeholder.com/400x300/999999/ffffff?text=No+Scan+Image'">
                            </div>
                        ` : `
                            <div class="no-scan-image">
                                <i class="fas fa-image"></i>
                                <p>No scan image available</p>
                            </div>
                        `}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    comparisonModal.innerHTML = modalContent;
    
    // Add to document
    document.body.appendChild(comparisonModal);
    
    // Add zoom functionality to scan image with proper bounds
    if (scanImageUrl) {
        const scanImage = comparisonModal.querySelector('.scan-comparison-image');
        const imageContainer = comparisonModal.querySelector('.scan-image-container');
        
        if (scanImage && imageContainer) {
            let scale = 1;
            let isDragging = false;
            let startX, startY, translateX = 0, translateY = 0;
            
            // Function to constrain translation within bounds
            const constrainTranslation = () => {
                const containerRect = imageContainer.getBoundingClientRect();
                
                // Get original image dimensions
                const imageNaturalWidth = scanImage.naturalWidth || scanImage.width;
                const imageNaturalHeight = scanImage.naturalHeight || scanImage.height;
                
                // Calculate scaled image dimensions
                const scaledWidth = imageNaturalWidth * scale;
                const scaledHeight = imageNaturalHeight * scale;
                
                // Calculate max translation boundaries based on scaled size
                const maxTranslateX = Math.max(0, (scaledWidth - containerRect.width) / (2 * scale));
                const maxTranslateY = Math.max(0, (scaledHeight - containerRect.height) / (2 * scale));
                
                // Constrain translation to keep image within bounds
                translateX = Math.max(-maxTranslateX, Math.min(maxTranslateX, translateX));
                translateY = Math.max(-maxTranslateY, Math.min(maxTranslateY, translateY));
            };
            
            // Apply transform with constraints
            const applyTransform = () => {
                constrainTranslation();
                scanImage.style.transform = `scale(${scale}) translate(${translateX}px, ${translateY}px)`;
            };
            
            // Zoom with mouse wheel - zoom towards cursor position
            scanImage.addEventListener('wheel', (e) => {
                e.preventDefault();
                
                const containerRect = imageContainer.getBoundingClientRect();
                const delta = e.deltaY > 0 ? 0.9 : 1.1;
                const newScale = Math.max(0.5, Math.min(3, scale * delta));
                
                // Calculate cursor position relative to container center
                const cursorX = e.clientX - containerRect.left - containerRect.width / 2;
                const cursorY = e.clientY - containerRect.top - containerRect.height / 2;
                
                // Adjust translation to zoom towards cursor
                const scaleChange = newScale / scale;
                translateX = translateX * scaleChange + cursorX * (1 - scaleChange) / newScale;
                translateY = translateY * scaleChange + cursorY * (1 - scaleChange) / newScale;
                
                scale = newScale;
                applyTransform();
            });
            
            // Pan with mouse drag
            scanImage.addEventListener('mousedown', (e) => {
                e.preventDefault();
                isDragging = true;
                startX = e.clientX - translateX;
                startY = e.clientY - translateY;
                scanImage.style.cursor = 'grabbing';
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                translateX = e.clientX - startX;
                translateY = e.clientY - startY;
                applyTransform();
            });
            
            document.addEventListener('mouseup', () => {
                isDragging = false;
                if (scanImage) scanImage.style.cursor = 'grab';
            });
            
            // Initial setup
            scanImage.style.cursor = 'grab';
            scanImage.style.userSelect = 'none';
            scanImage.style.transformOrigin = 'center center';
            
            // Add double-click to reset
            scanImage.addEventListener('dblclick', () => {
                scale = 1;
                translateX = 0;
                translateY = 0;
                applyTransform();
            });
        }
    }
    
    // Add click outside to close
    comparisonModal.addEventListener('click', (e) => {
        if (e.target === comparisonModal) {
            closeImageComparison();
        }
    });
    
    // Add escape key handler
    document.addEventListener('keydown', handleImageComparisonEscape);
}

// Close image comparison dialog
function closeImageComparison() {
    const comparisonModal = document.getElementById('imageComparisonModal');
    if (comparisonModal) {
        document.removeEventListener('keydown', handleImageComparisonEscape);
        comparisonModal.remove();
    }
}

// Handle escape key for image comparison
function handleImageComparisonEscape(e) {
    if (e.key === 'Escape') {
        closeImageComparison();
    }
}

// Show full scan image for zero cards found
function showFullScanImage(fileName, imageUrl) {
    // Create full image modal
    const fullImageModal = document.createElement('div');
    fullImageModal.id = 'fullScanImageModal';
    fullImageModal.className = 'image-comparison-modal';
    
    const modalContent = `
        <div class="full-scan-content">
            <div class="full-scan-header">
                <h3>Scanned Image: ${fileName}</h3>
                <button class="close-btn" onclick="closeFullScanImage()">&times;</button>
            </div>
            <div class="full-scan-body">
                <div class="zoomable-scan-container">
                    <img src="${imageUrl}" alt="${fileName}" class="full-scan-image">
                </div>
            </div>
        </div>
    `;
    
    fullImageModal.innerHTML = modalContent;
    
    // Add to document
    document.body.appendChild(fullImageModal);
    
    // Add zoom functionality with proper bounds
    const scanImage = fullImageModal.querySelector('.full-scan-image');
    const imageContainer = fullImageModal.querySelector('.zoomable-scan-container');
    
    if (scanImage && imageContainer) {
        let scale = 1;
        let isDragging = false;
        let startX, startY, translateX = 0, translateY = 0;
        
        // Function to constrain translation within bounds
        const constrainTranslation = () => {
            const containerRect = imageContainer.getBoundingClientRect();
            
            // Get original image dimensions
            const imageNaturalWidth = scanImage.naturalWidth || scanImage.width;
            const imageNaturalHeight = scanImage.naturalHeight || scanImage.height;
            
            // Calculate scaled image dimensions
            const scaledWidth = imageNaturalWidth * scale;
            const scaledHeight = imageNaturalHeight * scale;
            
            // Calculate max translation boundaries based on scaled size
            const maxTranslateX = Math.max(0, (scaledWidth - containerRect.width) / (2 * scale));
            const maxTranslateY = Math.max(0, (scaledHeight - containerRect.height) / (2 * scale));
            
            // Constrain translation to keep image within bounds
            translateX = Math.max(-maxTranslateX, Math.min(maxTranslateX, translateX));
            translateY = Math.max(-maxTranslateY, Math.min(maxTranslateY, translateY));
        };
        
        // Apply transform with constraints
        const applyTransform = () => {
            constrainTranslation();
            scanImage.style.transform = `scale(${scale}) translate(${translateX}px, ${translateY}px)`;
        };
        
        // Zoom with mouse wheel - zoom towards cursor position
        scanImage.addEventListener('wheel', (e) => {
            e.preventDefault();
            
            const containerRect = imageContainer.getBoundingClientRect();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            const newScale = Math.max(0.3, Math.min(5, scale * delta));
            
            // Calculate cursor position relative to container center
            const cursorX = e.clientX - containerRect.left - containerRect.width / 2;
            const cursorY = e.clientY - containerRect.top - containerRect.height / 2;
            
            // Adjust translation to zoom towards cursor
            const scaleChange = newScale / scale;
            translateX = translateX * scaleChange + cursorX * (1 - scaleChange) / newScale;
            translateY = translateY * scaleChange + cursorY * (1 - scaleChange) / newScale;
            
            scale = newScale;
            applyTransform();
        });
        
        // Pan with mouse drag
        scanImage.addEventListener('mousedown', (e) => {
            e.preventDefault();
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
            scanImage.style.cursor = 'grabbing';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            applyTransform();
        });
        
        document.addEventListener('mouseup', () => {
            isDragging = false;
            if (scanImage) scanImage.style.cursor = 'grab';
        });
        
        // Initial setup
        scanImage.style.cursor = 'grab';
        scanImage.style.userSelect = 'none';
        scanImage.style.transformOrigin = 'center center';
        
        // Add double-click to reset
        scanImage.addEventListener('dblclick', () => {
            scale = 1;
            translateX = 0;
            translateY = 0;
            applyTransform();
        });
    }
    
    // Add click outside to close
    fullImageModal.addEventListener('click', (e) => {
        if (e.target === fullImageModal) {
            closeFullScanImage();
        }
    });
    
    // Add escape key handler
    document.addEventListener('keydown', handleFullScanEscape);
}

// Close full scan image dialog
function closeFullScanImage() {
    const fullImageModal = document.getElementById('fullScanImageModal');
    if (fullImageModal) {
        document.removeEventListener('keydown', handleFullScanEscape);
        fullImageModal.remove();
    }
}

// Handle escape key for full scan image
function handleFullScanEscape(e) {
    if (e.key === 'Escape') {
        closeFullScanImage();
    }
}

// Tools dropdown functionality
function toggleToolsMenu() {
    const dropdown = document.getElementById('toolsDropdown');
    dropdown.classList.toggle('show');
}

// Close tools dropdown when clicking outside
document.addEventListener('click', function(event) {
    const toolsContainer = document.querySelector('.tools-container');
    const dropdown = document.getElementById('toolsDropdown');
    
    if (!toolsContainer.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// Scan History functionality
async function showScanHistory() {
    // Close tools dropdown
    const dropdown = document.getElementById('toolsDropdown');
    dropdown.classList.remove('show');
    
    // Show modal
    const modal = document.getElementById('scanHistoryModal');
    modal.style.display = 'flex';
    
    // Load scan history data
    await loadScanHistory();
}

function closeScanHistoryModal() {
    const modal = document.getElementById('scanHistoryModal');
    modal.style.display = 'none';
}

async function loadScanHistory() {
    const body = document.getElementById('scanHistoryBody');
    
    // Show loading state
    body.innerHTML = `
        <div class="scan-history-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading scan history...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/scan/history');
        if (!response.ok) {
            throw new Error('Failed to load scan history');
        }
        
        const scanHistory = await response.json();
        displayScanHistory(scanHistory);
        
    } catch (error) {
        console.error('Error loading scan history:', error);
        body.innerHTML = `
            <div class="empty-scan-history">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error Loading History</h3>
                <p>Failed to load scan history. Please try again.</p>
            </div>
        `;
    }
}

function displayScanHistory(scanHistory) {
    const body = document.getElementById('scanHistoryBody');
    
    if (!scanHistory.scans || scanHistory.scans.length === 0) {
        body.innerHTML = `
            <div class="empty-scan-history">
                <i class="fas fa-history"></i>
                <h3>No Scan History</h3>
                <p>You haven't performed any scans yet. Start by uploading some card images!</p>
            </div>
        `;
        return;
    }
    
    const scansHtml = scanHistory.scans.map(scan => createScanHistoryItem(scan)).join('');
    
    body.innerHTML = `
        <div class="scan-history-list">
            ${scansHtml}
        </div>
    `;
}

function createScanHistoryItem(scan) {
    const scanDate = new Date(scan.created_at);
    const formattedDate = scanDate.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
    const formattedTime = scanDate.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const imagesHtml = scan.images && scan.images.length > 0 
        ? scan.images.map(image => `
            <img src="/uploads/${image.filename}" 
                 alt="Scan image" 
                 class="scan-thumbnail"
                 onclick="showFullScanImage('${image.filename}', '/uploads/${image.filename}')"
                 title="${image.original_filename}">
        `).join('')
        : '<p style="color: #999; font-style: italic;">No images available</p>';
    
    const cardsHtml = scan.cards && scan.cards.length > 0
        ? scan.cards.map(card => `
            <div class="scan-card-item">
                <i class="fas fa-check-circle"></i>
                <span>${card.name} (${card.set_name})</span>
            </div>
        `).join('')
        : '<p style="color: #999; font-style: italic;">No cards identified</p>';
    
    const statusText = scan.status === 'completed' ? 'Completed' : scan.status === 'failed' ? 'Failed' : 'In Progress';
    const statusColor = scan.status === 'completed' ? '#28a745' : scan.status === 'failed' ? '#dc3545' : '#ffc107';
    
    return `
        <div class="scan-item">
            <div class="scan-header">
                <div class="scan-info">
                    <h4>Scan #${scan.id}</h4>
                    <div class="scan-meta">
                        ${formattedDate} at ${formattedTime} • 
                        <span style="color: ${statusColor}; font-weight: 500;">${statusText}</span>
                    </div>
                </div>
                <div class="scan-stats">
                    <div>${scan.total_images || 0} images</div>
                    <div>${scan.cards_count || 0} cards found</div>
                </div>
            </div>
            
            ${scan.images && scan.images.length > 0 ? `
                <div class="scan-images">
                    ${imagesHtml}
                </div>
            ` : ''}
            
            ${scan.cards && scan.cards.length > 0 ? `
                <div class="scan-cards">
                    <h5>Cards Found (${scan.cards.length})</h5>
                    <div class="scan-cards-list">
                        ${cardsHtml}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
} 