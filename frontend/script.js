// Global variables
let cards = [];
let searchTerm = '';
let currentCardIndex = 0;
let viewMode = 'individual'; // 'individual' or 'stacked'
let currentScan = null;
let scanPollingInterval = null;
let fileInputBusy = false; // Flag to prevent multiple file input clicks
let fileInputTimeout = null; // Timeout to reset busy flag

// Sorting variables
let sortField = 'name'; // Default sort field
let sortDirection = 'asc'; // 'asc' or 'desc'

// Camera variables
let cameraStream = null;
let cameraModal = null;
let cameraVideo = null;
let cameraCanvas = null;

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
    checkEnvironment();
    setupEventListeners();
    initializeCamera();
    initializeSortUI();
    loadCards();
    loadStats();
    addTestData(); // Add test data with real Magic cards
    console.log('🚀 DEBUG: Application initialization complete');
});

// Check and display environment information
async function checkEnvironment() {
    try {
        const response = await fetch('/api/environment');
        const envInfo = await response.json();
        
        console.log(`🌍 Environment: ${envInfo.environment.toUpperCase()}`);
        console.log(`🌐 Port: ${envInfo.port}`);
        console.log(`🛠️ Development Mode: ${envInfo.is_development}`);
        
        // Store environment info globally for other functions to use
        window.environmentInfo = envInfo;
        
        // Add environment badge to header if in development
        if (envInfo.is_development) {
            const header = document.querySelector('.header');
            if (header) {
                const badge = document.createElement('div');
                badge.className = 'environment-badge';
                badge.innerHTML = '🛠️ Development Mode - Port ' + envInfo.port;
                badge.style.cssText = `
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 500;
                    margin-top: 10px;
                    display: inline-block;
                `;
                header.appendChild(badge);
            }
        }
    } catch (error) {
        console.error('Failed to fetch environment info:', error);
    }
}

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
            handleUploadButtonClick();
        });
    }
    
    // Upload area click handler (only if not clicking the button)
    uploadArea.addEventListener('click', (e) => {
        if (e.target !== uploadBtn && !uploadBtn.contains(e.target)) {
            handleUploadButtonClick();
        }
    });
    
    const cameraBtn = document.getElementById('cameraBtn');
    if (cameraBtn) {
        cameraBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            handleCameraClick();
        });
    }
    
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    
    console.log('🎧 DEBUG: Adding change event listener to file input');
    fileInput.addEventListener('change', handleFileSelect);
    
    // Add mobile-specific event listeners to handle file input issues
    fileInput.addEventListener('focus', handleFileInputFocus);
    fileInput.addEventListener('blur', handleFileInputBlur);
    
    // Add visibility change listener to reset busy flag when user returns to app
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
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
            // Only navigate if card modal is open
            if (cardModal.style.display === 'block') {
                navigateCard(-1);
            }
        } else if (e.key === 'ArrowRight') {
            // Only navigate if card modal is open
            if (cardModal.style.display === 'block') {
                navigateCard(1);
            }
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

// Handle upload button click with improved mobile support
function handleUploadButtonClick() {
    // Check if file input is busy
    if (fileInputBusy) {
        console.log('🔘 DEBUG: File input busy, ignoring button click');
        return;
    }
    
    console.log('🔘 DEBUG: Upload button clicked, triggering file input click');
    setFileInputBusy(true);
    fileInput.click();
}

// Set file input busy state with timeout fallback
function setFileInputBusy(busy) {
    fileInputBusy = busy;
    
    // Clear any existing timeout
    if (fileInputTimeout) {
        clearTimeout(fileInputTimeout);
        fileInputTimeout = null;
    }
    
    if (busy) {
        // Set a timeout to automatically reset the busy flag
        // This prevents the button from being permanently disabled
        fileInputTimeout = setTimeout(() => {
            console.log('🔘 DEBUG: File input timeout reached, resetting busy flag');
            fileInputBusy = false;
            fileInputTimeout = null;
        }, 5000); // 5 second timeout
    }
}

// Handle file input focus (when file picker opens)
function handleFileInputFocus() {
    console.log('🔍 DEBUG: File input focused (file picker opened)');
}

// Handle file input blur (when file picker closes)
function handleFileInputBlur() {
    console.log('🔍 DEBUG: File input blurred (file picker closed)');
    // Small delay to allow change event to fire first
    setTimeout(() => {
        if (fileInputBusy) {
            console.log('🔍 DEBUG: File input still busy after blur, resetting');
            setFileInputBusy(false);
        }
    }, 100);
}

// Handle visibility change (when user returns to app)
function handleVisibilityChange() {
    if (!document.hidden) {
        console.log('🔍 DEBUG: App became visible, checking file input state');
        // Reset busy flag when user returns to app
        // This handles cases where mobile doesn't fire proper events
        setTimeout(() => {
            if (fileInputBusy) {
                console.log('🔍 DEBUG: Resetting file input busy flag after visibility change');
                setFileInputBusy(false);
            }
        }, 500);
    }
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
    setFileInputBusy(true);
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
        setFileInputBusy(false);
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
            setFileInputBusy(false); // Reset busy flag
            console.log('🔄 DEBUG: File input reset complete');
        }, 100);
    } else {
        console.log('🔄 DEBUG: File input not found!');
        setFileInputBusy(false); // Reset busy flag even if input not found
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
        // Show immediate upload progress
        showUploadProgress();
        updateProgress(10, `Uploading ${imageFiles.length} image${imageFiles.length > 1 ? 's' : ''}...`);
        
        // Start the new scan workflow
        const scanResult = await uploadAndScan(imageFiles);
        
        if (scanResult.success) {
            console.log('📁 DEBUG: Scan created successfully:', scanResult);
            updateProgress(100, 'Upload complete! Starting scan...');
            
            // Brief delay to show completion, then hide progress
            setTimeout(() => {
                hideUploadProgress();
            }, 800);
            
            // Reset file input after successful scan creation
            resetFileInput();
            // Open scanning modal and start the workflow (non-blocking)
            await showScanningModal(scanResult.scan_id, imageFiles);
        } else {
            console.log('📁 DEBUG: Scan creation failed:', scanResult.error);
            hideUploadProgress();
            alert(`Error starting scan: ${scanResult.error}`);
            resetFileInput();
        }
        
    } catch (error) {
        console.error('📁 DEBUG: Error in processFiles:', error);
        hideUploadProgress();
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
        updateProgress(30, 'Sending files to server...');
        
        const response = await fetch('/upload/scan', {
            method: 'POST',
            body: formData
        });
        
        updateProgress(60, 'Processing upload...');
        
        if (!response.ok) {
            let errorMessage = 'Failed to upload files';
            try {
                // Clone the response to avoid "body stream already read" error
                const responseClone = response.clone();
                // Try to parse as JSON first
                const errorData = await response.json();
                errorMessage = errorData.detail || errorData.error || errorMessage;
            } catch (e) {
                try {
                    // If JSON parsing fails, try to read as text using clone
                    const errorText = await responseClone.text();
                errorMessage = errorText || errorMessage;
                } catch (textError) {
                    // If both JSON and text parsing fail, use the original error message
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }
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
                    $${getConditionAdjustedPrice(card.price_usd || 0, card.condition).toFixed(2)}
                </span>
                <span class="price price-eur">
                    <i class="fas fa-euro-sign"></i>
                    €${getConditionAdjustedPrice(card.price_eur || 0, card.condition).toFixed(2)}
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
        // and create individual cards for singles using proper individual card data
        filteredCards.forEach((card, index) => {
            if (card.total_cards > 1) {
                const cardElement = createMiniFannedStack(card, index, filteredCards);
                cardsGrid.appendChild(cardElement);
            } else {
                // For single cards in stacked view, create a proper individual card
                // using the duplicate entry data merged with stack data
                if (card.duplicates && card.duplicates[0]) {
                    const duplicateData = card.duplicates[0];
                    const individualCard = {
                        id: duplicateData.id,
                        unique_id: duplicateData.unique_id,
                        name: card.name,
                        set_name: duplicateData.set_name || card.set_name,
                        set_code: duplicateData.set_code || card.set_code,
                        collector_number: duplicateData.collector_number || card.collector_number,
                        rarity: card.rarity,
                        mana_cost: card.mana_cost,
                        type_line: card.type_line,
                        oracle_text: card.oracle_text,
                        flavor_text: card.flavor_text,
                        power: card.power,
                        toughness: card.toughness,
                        colors: card.colors,
                        price_usd: card.price_usd,
                        price_eur: card.price_eur,
                        price_tix: card.price_tix,
                        count: duplicateData.count,
                        stack_count: card.stack_count,
                        stack_id: card.stack_id,
                        first_seen: duplicateData.first_seen,
                        last_seen: duplicateData.last_seen,
                        image_url: card.image_url,
                        notes: duplicateData.notes,
                        condition: duplicateData.condition,
                        is_example: duplicateData.is_example,
                        duplicate_group: card.duplicate_group,
                        first_seen: duplicateData.first_seen,
                        last_seen: duplicateData.last_seen,
                        added_method: duplicateData.added_method,
                        scan_id: card.scan_id || duplicateData.scan_id
                    };
                    
                    // Create an individual-style filtered array for this single card
                    const individualFilteredCards = [individualCard];
                    const cardElement = createDatabaseCard(individualCard, 0, individualFilteredCards);
                    cardsGrid.appendChild(cardElement);
                } else {
                    // Fallback for cards without duplicate data
                    const cardElement = createDatabaseCard(card, index, [card]);
                    cardsGrid.appendChild(cardElement);
                }
            }
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
    
    // Calculate values
    const individualValue = getConditionAdjustedPrice(card.price_usd || 0, card.condition);
    const combinedValue = individualValue * (card.total_cards || 1);
    
    // Create stack count badge
    const stackBadge = card.total_cards > 1 ? `<div class="stack-count-badge">×${card.total_cards}</div>` : '';
    
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
            <div class="card-count">$${combinedValue.toFixed(2)} ($${individualValue.toFixed(2)})</div>
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
            <div class="card-count">$${getConditionAdjustedPrice(parentCard.price_usd || 0, cardData.condition).toFixed(2)}</div>
            <div class="card-added">
                Added: ${formatDateTime(cardData.first_seen)} (${formatAddedMethod(cardData.added_method)})
            </div>
            ${cardData.added_method === 'SCANNED' && cardData.scan_id ? `
            <div class="spread-scan-section">
                <button class="view-scan-btn-small-prominent" onclick="viewScanImage(${cardData.scan_id}, '${parentCard.name}')" title="View original scanned image">
                    <i class="fas fa-eye"></i>
                    View Scan
                </button>
            </div>
            ` : ''}
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
        unique_id: cardData.unique_id,
        count: cardData.count,
        condition: cardData.condition,
        notes: cardData.notes,
        is_example: cardData.is_example,
        first_seen: cardData.first_seen,
        last_seen: cardData.last_seen
    };
    
    // Create navigation array with only cards from this stack
    const stackCards = [];
    if (parentCard.duplicates) {
        parentCard.duplicates.forEach((duplicate, index) => {
            stackCards.push({
                ...parentCard,
                id: duplicate.id,
                unique_id: duplicate.unique_id,
                count: duplicate.count,
                condition: duplicate.condition,
                notes: duplicate.notes,
                is_example: duplicate.is_example,
                first_seen: duplicate.first_seen,
                last_seen: duplicate.last_seen
            });
        });
    }
    
    // Find the current card's index in the stack
    const currentIndex = stackCards.findIndex(card => card.id === cardData.id);
    currentCardIndex = currentIndex >= 0 ? currentIndex : 0;
    
    // Show card details modal with stack navigation
    modalTitle.textContent = combinedCard.name;
    modalBody.innerHTML = createEnhancedCardDetailHTML(combinedCard, stackCards);
    
    // Add navigation arrows if there are multiple cards in stack
    if (stackCards.length > 1) {
        addNavigationArrows(stackCards);
    }
    
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
    // Handle null, undefined, or empty colors
    if (!colors || colors === '' || colors === null) return 'colorless';
    
    // Handle arrays (sometimes colors come as arrays)
    if (Array.isArray(colors)) {
        if (colors.length === 0) return 'colorless';
        if (colors.length > 1) return 'multicolor';
        const color = colors[0].toString().trim().toUpperCase();
        switch (color) {
            case 'W': return 'white';
            case 'U': return 'blue';
            case 'B': return 'black';
            case 'R': return 'red';
            case 'G': return 'green';
            default: return 'colorless';
        }
    }
    
    // Handle string format
    const colorArray = colors.toString().split(',').map(c => c.trim().toUpperCase()).filter(c => c);
    
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
    
    // Calculate card value with condition adjustment
    const cardValue = getConditionAdjustedPrice(card.price_usd || 0, card.condition);
    const cardCount = card.count || 1;
    
    // Create count multiplier badge (only show if count > 1)
    const countBadge = cardCount > 1 ? `<div class="count-badge">×${cardCount}</div>` : '';
    
    cardDiv.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
            ${exampleBadge}
            ${countBadge}
        </div>
        <div class="card-info">
            <div class="card-name">${card.name}</div>
            <div class="card-set">${card.set_name || 'Unknown Set'}</div>
            <div class="card-count">$${cardValue.toFixed(2)}</div>
        </div>
    `;
    
    return cardDiv;
}



// Filter cards based on search term
function filterCards() {
    let filteredCards = cards;
    
    // Apply search filter
    if (searchTerm) {
        filteredCards = filteredCards.filter(card => 
            card.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (card.set_name && card.set_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
            (card.notes && card.notes.toLowerCase().includes(searchTerm.toLowerCase()))
        );
    }
    
    // Apply sorting
    return sortCards(filteredCards);
}

// Sort cards based on current sort field and direction
function sortCards(cardsToSort) {
    if (!cardsToSort || cardsToSort.length === 0) return cardsToSort;
    
    return cardsToSort.sort((a, b) => {
        let aValue, bValue;
        
        switch (sortField) {
            case 'name':
                aValue = a.name || '';
                bValue = b.name || '';
                break;
                
            case 'set':
                aValue = a.set_name || '';
                bValue = b.set_name || '';
                break;
                
            case 'rarity':
                // Define rarity hierarchy
                const rarityOrder = { 'common': 1, 'uncommon': 2, 'rare': 3, 'mythic': 4, 'bonus': 5, 'special': 6, 'masterpiece': 7 };
                aValue = rarityOrder[a.rarity?.toLowerCase()] || 0;
                bValue = rarityOrder[b.rarity?.toLowerCase()] || 0;
                break;
                
            case 'price':
                aValue = parseFloat(a.price_usd) || 0;
                bValue = parseFloat(b.price_usd) || 0;
                break;
                
            case 'count':
                // Use stack_count for stacked view, count for individual view
                aValue = viewMode === 'stacked' ? (a.stack_count || a.total_cards || 1) : (a.count || 1);
                bValue = viewMode === 'stacked' ? (b.stack_count || b.total_cards || 1) : (b.count || 1);
                break;
                
            case 'condition':
                // Define condition hierarchy
                const conditionOrder = { 'NM': 1, 'LP': 2, 'MP': 3, 'HP': 4, 'DMG': 5 };
                aValue = conditionOrder[a.condition] || 0;
                bValue = conditionOrder[b.condition] || 0;
                break;
                
            case 'date':
                aValue = new Date(a.first_seen || a.last_seen || 0);
                bValue = new Date(b.first_seen || b.last_seen || 0);
                break;
                
            case 'mana':
                aValue = calculateManaCost(a.mana_cost);
                bValue = calculateManaCost(b.mana_cost);
                break;
                
            case 'color':
                aValue = getColorSortValue(a.colors);
                bValue = getColorSortValue(b.colors);
                break;
                
            case 'type':
                aValue = a.type_line || '';
                bValue = b.type_line || '';
                break;
                
            default:
                aValue = a.name || '';
                bValue = b.name || '';
        }
        
        // Handle different data types
        let comparison = 0;
        if (typeof aValue === 'string' && typeof bValue === 'string') {
            comparison = aValue.localeCompare(bValue);
        } else if (typeof aValue === 'number' && typeof bValue === 'number') {
            comparison = aValue - bValue;
        } else if (aValue instanceof Date && bValue instanceof Date) {
            comparison = aValue.getTime() - bValue.getTime();
        } else {
            // Fallback to string comparison
            comparison = String(aValue).localeCompare(String(bValue));
        }
        
        return sortDirection === 'asc' ? comparison : -comparison;
    });
}

// Calculate converted mana cost for sorting
function calculateManaCost(manaCost) {
    if (!manaCost) return 0;
    
    // Extract numbers from mana cost string
    const numbers = manaCost.match(/\d+/g);
    if (!numbers) return 0;
    
    return numbers.reduce((sum, num) => sum + parseInt(num), 0);
}

// Get color sort value (WUBRG order)
function getColorSortValue(colors) {
    if (!colors || colors.length === 0) return 'Z'; // Colorless goes last
    
    const colorOrder = { 'W': 1, 'U': 2, 'B': 3, 'R': 4, 'G': 5 };
    const colorArray = Array.isArray(colors) ? colors : JSON.parse(colors || '[]');
    
    if (colorArray.length === 0) return 'Z'; // Colorless
    if (colorArray.length > 1) return 'A'; // Multicolor goes first
    
    return String.fromCharCode(64 + (colorOrder[colorArray[0]] || 6)); // Single colors
}

// Handle search input
function handleSearch(e) {
    searchTerm = e.target.value;
    displayCards();
}

// Show database status modal
async function showDatabaseStatus() {
    const modal = document.getElementById('cardModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    
    modalTitle.textContent = 'Database & Storage Status';
    modalBody.innerHTML = `
        <div class="database-status-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading database status...</p>
        </div>
    `;
    
    modal.style.display = 'block';
    
    try {
        const response = await fetch('/api/database/status');
        const status = await response.json();
        
        if (status.error) {
            modalBody.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Error Loading Database Status</h3>
                    <p>${status.error}</p>
                </div>
            `;
            
            // Remove any existing navigation arrows
            const existingArrows = document.querySelectorAll('.nav-arrow');
            existingArrows.forEach(arrow => arrow.remove());
            return;
        }
        
        modalBody.innerHTML = createDatabaseStatusHTML(status);
        
        // Remove any existing navigation arrows (they shouldn't be in database status)
        const existingArrows = document.querySelectorAll('.nav-arrow');
        existingArrows.forEach(arrow => arrow.remove());
        
    } catch (error) {
        console.error('Error loading database status:', error);
        modalBody.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Connection Error</h3>
                <p>Unable to load database status. Please check your connection.</p>
            </div>
        `;
        
        // Remove any existing navigation arrows
        const existingArrows = document.querySelectorAll('.nav-arrow');
        existingArrows.forEach(arrow => arrow.remove());
    }
}

// Create database status HTML
function createDatabaseStatusHTML(status) {
    const { database, storage, statistics, recent_activity, environment } = status;
    
    return `
        <div class="database-status-content">
            <!-- Database Information -->
            <div class="status-section">
                <h3><i class="fas fa-database"></i> Database Information</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <label>Database Type:</label>
                        <span class="status-value ${database.is_cloud ? 'cloud' : 'local'}">${database.type}</span>
                    </div>
                    <div class="status-item">
                        <label>Location:</label>
                        <span class="status-value">${database.location}</span>
                    </div>
                    <div class="status-item">
                        <label>Database Size:</label>
                        <span class="status-value">${database.file_size}</span>
                    </div>
                    ${database.url ? `
                    <div class="status-item full-width">
                        <label>Connection URL:</label>
                        <span class="status-value code">${database.url}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Storage Information -->
            <div class="status-section">
                <h3><i class="fas fa-folder-open"></i> File Storage</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <label>Storage Type:</label>
                        <span class="status-value ${storage.uses_railway_files ? 'cloud' : 'local'}">${storage.type}</span>
                    </div>
                    <div class="status-item">
                        <label>Total Files:</label>
                        <span class="status-value">${storage.total_files}</span>
                    </div>
                    <div class="status-item">
                        <label>Total Size:</label>
                        <span class="status-value">${storage.total_size}</span>
                    </div>
                    <div class="status-item full-width">
                        <label>Storage Path:</label>
                        <span class="status-value code">${storage.path}</span>
                    </div>
                    ${storage.railway_url ? `
                    <div class="status-item full-width">
                        <label>Railway URL:</label>
                        <span class="status-value code">${storage.railway_url}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Statistics -->
            <div class="status-section">
                <h3><i class="fas fa-chart-bar"></i> Statistics</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <label>Total Cards:</label>
                        <span class="status-value highlight">${statistics.total_cards}</span>
                    </div>
                    <div class="status-item">
                        <label>Total Scans:</label>
                        <span class="status-value highlight">${statistics.total_scans}</span>
                    </div>
                    <div class="status-item">
                        <label>Card Entries:</label>
                        <span class="status-value highlight">${statistics.total_card_entries}</span>
                    </div>
                    <div class="status-item">
                        <label>Cards per Scan:</label>
                        <span class="status-value">${statistics.cards_per_scan}</span>
                    </div>
                </div>
            </div>
            
            <!-- Environment -->
            <div class="status-section">
                <h3><i class="fas fa-cog"></i> Environment</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <label>Environment:</label>
                        <span class="status-value ${environment.env_mode === 'development' ? 'dev' : 'prod'}">${environment.env_mode}</span>
                    </div>
                    <div class="status-item">
                        <label>Port:</label>
                        <span class="status-value">${environment.port}</span>
                    </div>
                    <div class="status-item">
                        <label>OpenAI API:</label>
                        <span class="status-value ${environment.openai_configured ? 'configured' : 'missing'}">${environment.openai_configured ? 'Configured' : 'Not Configured'}</span>
                    </div>
                    ${environment.railway_environment ? `
                    <div class="status-item">
                        <label>Railway Env:</label>
                        <span class="status-value">${environment.railway_environment}</span>
                    </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Recent Activity -->
            <div class="status-section">
                <h3><i class="fas fa-clock"></i> Recent Activity</h3>
                
                <div class="activity-subsection">
                    <h4>Recent Cards Added</h4>
                    <div class="activity-list">
                        ${recent_activity.recent_cards.length > 0 ? recent_activity.recent_cards.map(card => `
                            <div class="activity-item">
                                <div class="activity-main">
                                    <strong>${card.name}</strong>
                                    <span class="activity-set">${card.set_name || 'Unknown Set'}</span>
                                </div>
                                <div class="activity-meta">
                                    <span class="activity-method">${card.added_method || 'Unknown'}</span>
                                    <span class="activity-date">${formatDateTime(card.first_seen)}</span>
                                </div>
                            </div>
                        `).join('') : '<div class="activity-item">No recent cards</div>'}
                    </div>
                </div>
                
                <div class="activity-subsection">
                    <h4>Recent Scans</h4>
                    <div class="activity-list">
                        ${recent_activity.recent_scans.length > 0 ? recent_activity.recent_scans.map(scan => `
                            <div class="activity-item">
                                <div class="activity-main">
                                    <strong>Scan #${scan.scan_id}</strong>
                                </div>
                                <div class="activity-meta">
                                    <span class="activity-cards">${scan.total_cards_found || 0} cards found</span>
                                    <span class="activity-date">${formatDateTime(scan.created_at)}</span>
                                </div>
                            </div>
                        `).join('') : '<div class="activity-item">No recent scans</div>'}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/stats');
        const stats = await response.json();
        
        // Always show total stats (including examples) to give accurate count
        document.getElementById('totalCards').textContent = stats.total_cards;
        document.getElementById('totalCount').textContent = stats.total_count;
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
    modalBody.innerHTML = createEnhancedCardDetailHTML(card, cardsToUse);
    
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
        
        // Add visual transition effect
        const cardImage = modalBody.querySelector('.card-image-large');
        if (cardImage) {
            cardImage.style.opacity = '0.3';
            setTimeout(() => {
                cardImage.style.opacity = '1';
            }, 150);
        }
        
        modalTitle.textContent = card.name;
        modalBody.innerHTML = createEnhancedCardDetailHTML(card, filteredCards);
        
        // Update navigation arrows
        addNavigationArrows(filteredCards);
        
        // Flash the modal content briefly to indicate change
        modalBody.style.backgroundColor = '#f0f8ff';
        setTimeout(() => {
            modalBody.style.backgroundColor = '';
        }, 200);
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

// Calculate condition-adjusted price
function getConditionAdjustedPrice(basePrice, condition) {
    const multiplier = CONDITION_MULTIPLIERS[condition] || CONDITION_MULTIPLIERS['UNKNOWN'];
    return basePrice * multiplier;
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
    
    // Calculate total value with condition adjustments
    const totalValue = cards.reduce((sum, card) => {
        const adjustedPrice = getConditionAdjustedPrice(card.price_usd || 0, card.condition);
        return sum + (adjustedPrice * (card.count || 0));
    }, 0);
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

// Condition multipliers for realistic pricing
const CONDITION_MULTIPLIERS = {
    'NM': 1.0,      // Near Mint: 100%
    'LP': 0.85,     // Lightly Played: 85%
    'MP': 0.70,     // Moderately Played: 70%
    'HP': 0.50,     // Heavily Played: 50%
    'DMG': 0.35,    // Damaged: 35%
    'UNKNOWN': 0.85 // Conservative estimate
};

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
    { value: 'vma', label: 'Vintage Masters', code: 'VMA' },
    { value: 'm12', label: 'Magic 2012', code: 'M12' },
    { value: 'cmd', label: 'Commander 2011', code: 'CMD' },
    { value: 'cma', label: 'Commander Anthology', code: 'CMA' },
    { value: 'mm2', label: 'Modern Masters 2015', code: 'MM2' },
    { value: 'tsr', label: 'Time Spiral Remastered', code: 'TSR' },
    { value: 'uma', label: 'Ultimate Masters', code: 'UMA' },
    { value: 'ema', label: 'Eternal Masters', code: 'EMA' },
    { value: 'mh2', label: 'Modern Horizons 2', code: 'MH2' },
    { value: 'cmm', label: 'Commander Masters', code: 'CMM' },
    { value: 'who', label: 'Doctor Who', code: 'WHO' },
    { value: 'pip', label: 'Fallout', code: 'PIP' },
    { value: 'mh1', label: 'Modern Horizons', code: 'MH1' },
    { value: 'mm3', label: 'Modern Masters 2017', code: 'MM3' },
    { value: 'rtr', label: 'Return to Ravnica', code: 'RTR' },
    { value: 'jmp', label: 'Jumpstart', code: 'JMP' },
    { value: 'j21', label: 'Jumpstart: Historic Horizons', code: 'J21' },
    { value: 'j22', label: 'Jumpstart 2022', code: 'J22' },
    { value: 'c13', label: 'Commander 2013', code: 'C13' },
    { value: 'c14', label: 'Commander 2014', code: 'C14' },
    { value: 'c15', label: 'Commander 2015', code: 'C15' },
    { value: 'c16', label: 'Commander 2016', code: 'C16' },
    { value: 'c17', label: 'Commander 2017', code: 'C17' },
    { value: 'c18', label: 'Commander 2018', code: 'C18' },
    { value: 'c19', label: 'Commander 2019', code: 'C19' },
    { value: 'c20', label: 'Commander 2020', code: 'C20' },
    { value: 'c21', label: 'Commander 2021', code: 'C21' },
    { value: 'ncc', label: 'Streets of New Capenna Commander', code: 'NCC' },
    { value: 'clb', label: 'Commander Legends: Battle for Baldur\'s Gate', code: 'CLB' },
    { value: 'dmc', label: 'Dominaria United Commander', code: 'DMC' },
    { value: 'brc', label: 'The Brothers\' War Commander', code: 'BRC' },
    { value: 'onc', label: 'Phyrexia: All Will Be One Commander', code: 'ONC' },
    { value: 'moc', label: 'March of the Machine Commander', code: 'MOC' },
    { value: 'ltc', label: 'The Lord of the Rings: Tales of Middle-earth Commander', code: 'LTC' },
    { value: 'woc', label: 'Wilds of Eldraine Commander', code: 'WOC' },
    { value: 'lcc', label: 'The Lost Caverns of Ixalan Commander', code: 'LCC' },
    { value: 'mkc', label: 'Murders at Karlov Manor Commander', code: 'MKC' },
    { value: 'otc', label: 'Outlaws of Thunder Junction Commander', code: 'OTC' },
    { value: 'blc', label: 'Bloomburrow Commander', code: 'BLC' },
    { value: 'fdnc', label: 'Foundations Commander', code: 'FDNC' },
    { value: 'acr', label: 'Assassin\'s Creed', code: 'ACR' },
    { value: 'jou', label: 'Journey into Nyx', code: 'JOU' },
    { value: 'sld', label: 'Secret Lair Drop', code: 'SLD' },
    { value: 'prm', label: 'Promotional Cards', code: 'PRM' },
    { value: 'plist', label: 'The List', code: 'PLIST' },
    { value: 'mb1', label: 'Mystery Booster', code: 'MB1' },
    { value: 'mb2', label: 'Mystery Booster 2', code: 'MB2' },
    { value: 'unf', label: 'Unfinity', code: 'UNF' },
    { value: 'und', label: 'Undrafted', code: 'UND' },
    { value: 'clue', label: 'Clue Edition', code: 'CLUE' },
    { value: 'rex', label: 'Jurassic World Collection', code: 'REX' },
    { value: 'fbb', label: 'Foreign Black Border', code: 'FBB' },
    { value: 'ced', label: 'Collector\'s Edition', code: 'CED' },
    { value: 'cei', label: 'International Collector\'s Edition', code: 'CEI' },
    { value: 'me1', label: 'Masters Edition', code: 'ME1' },
    { value: 'me2', label: 'Masters Edition II', code: 'ME2' },
    { value: 'me3', label: 'Masters Edition III', code: 'ME3' },
    { value: 'me4', label: 'Masters Edition IV', code: 'ME4' },
    { value: 'avr', label: 'Avacyn Restored', code: 'AVR' },
    { value: 'ddm', label: 'Duel Decks: Merfolk vs. Goblins', code: 'DDM' },
    { value: 'pca', label: 'Planechase Anthology', code: 'PCA' },
    { value: 'arc', label: 'Archenemy', code: 'ARC' },
    { value: 'hop', label: 'Planechase', code: 'HOP' },
    { value: 'pc2', label: 'Planechase 2012', code: 'PC2' },
    { value: 'e01', label: 'Archenemy: Nicol Bolas', code: 'E01' },
    { value: 'e02', label: 'Explorers of Ixalan', code: 'E02' },
    { value: 'gk1', label: 'Global Series: Jiang Yanggu and Mu Yanling', code: 'GK1' },
    { value: 'gk2', label: 'Global Series: Jiang Yanggu and Mu Yanling', code: 'GK2' },
    { value: 'gs1', label: 'Global Series: Jiang Yanggu and Mu Yanling', code: 'GS1' },
    { value: 'spg', label: 'Special Guests', code: 'SPG' },
    { value: 'big', label: 'Big Furry Monster', code: 'BIG' },
    { value: 'und', label: 'Unsanctioned', code: 'UND' },
    { value: 'ust', label: 'Unstable', code: 'UST' },
    { value: 'unh', label: 'Unhinged', code: 'UNH' },
    { value: 'pf19', label: 'MagicFest 2019', code: 'PF19' },
    { value: 'pf20', label: 'MagicFest 2020', code: 'PF20' },
    { value: 'pf21', label: 'MagicFest 2021', code: 'PF21' },
    { value: 'pf22', label: 'MagicFest 2022', code: 'PF22' },
    { value: 'pf23', label: 'MagicFest 2023', code: 'PF23' },
    { value: 'pf24', label: 'MagicFest 2024', code: 'PF24' },
    { value: 'pf25', label: 'MagicFest 2025', code: 'PF25' },
    { value: 'phed', label: 'Phyrexia: All Will Be One Compleat Edition', code: 'PHED' },
    { value: 'sir', label: 'Shadows over Innistrad Remastered', code: 'SIR' },
    { value: 'mul', label: 'Multiverse Legends', code: 'MUL' },
    { value: 'lea', label: 'Limited Edition Alpha', code: 'LEA' },
    { value: 'leb', label: 'Limited Edition Beta', code: 'LEB' },
    { value: '2ed', label: 'Unlimited Edition', code: '2ED' },
    { value: '3ed', label: 'Revised Edition', code: '3ED' },
    { value: '4ed', label: 'Fourth Edition', code: '4ED' },
    { value: '5ed', label: 'Fifth Edition', code: '5ED' },
    { value: '6ed', label: 'Sixth Edition', code: '6ED' },
    { value: '7ed', label: 'Seventh Edition', code: '7ED' },
    { value: '8ed', label: 'Eighth Edition', code: '8ED' },
    { value: '9ed', label: 'Ninth Edition', code: '9ED' },
    { value: '10e', label: 'Tenth Edition', code: '10E' },
    { value: 'm10', label: 'Magic 2010', code: 'M10' },
    { value: 'm11', label: 'Magic 2011', code: 'M11' },
    { value: 'm13', label: 'Magic 2013', code: 'M13' },
    { value: 'm14', label: 'Magic 2014', code: 'M14' },
    { value: 'm15', label: 'Magic 2015', code: 'M15' },
    { value: 'ori', label: 'Magic Origins', code: 'ORI' },
    { value: 'aei', label: 'Aether Revolt Inventions', code: 'AEI' },
    { value: 'mps', label: 'Kaladesh Inventions', code: 'MPS' },
    { value: 'exp', label: 'Zendikar Expeditions', code: 'EXP' },
    { value: 'gnt', label: 'Game Night', code: 'GNT' },
    { value: 'gn2', label: 'Game Night 2019', code: 'GN2' },
    { value: 'gn3', label: 'Game Night: Free-for-All', code: 'GN3' },
    { value: 'cc1', label: 'Commander Collection: Green', code: 'CC1' },
    { value: 'cc2', label: 'Commander Collection: Black', code: 'CC2' },
    { value: 'ccn', label: 'Commander Collection: Neons', code: 'CCN' },
    { value: 'cmp', label: 'Commander Masters Preview', code: 'CMP' },
    { value: 'wth', label: 'Weatherlight', code: 'WTH' },
    { value: 'tbs', label: 'The Brothers\' War', code: 'TBS' },
    { value: 'gpt', label: 'Guildpact', code: 'GPT' },
    { value: 'pptq', label: 'Pro Tour Qualifier', code: 'PPTQ' },
    { value: 'pwp', label: 'Wizards Play Network', code: 'PWP' },
    { value: 'pfnm', label: 'Friday Night Magic', code: 'PFNM' },
    { value: 'pmtg', label: 'Magic Online Promos', code: 'PMTG' },
    { value: 'prel', label: 'Prerelease Events', code: 'PREL' },
    { value: 'pjgp', label: 'Judge Gift Program', code: 'PJGP' },
    { value: 'pwor', label: 'Worlds', code: 'PWOR' },
    { value: 'pnat', label: 'Nationals', code: 'PNAT' },
    { value: 'pptq', label: 'Pro Tour Qualifier', code: 'PPTQ' },
    { value: 'prtr', label: 'Return to Ravnica Promos', code: 'PRTR' },
    { value: 'pgtc', label: 'Gatecrash Promos', code: 'PGTC' },
    { value: 'pdgm', label: 'Dragon\'s Maze Promos', code: 'PDGM' },
    { value: 'pths', label: 'Theros Promos', code: 'PTHS' },
    { value: 'pbng', label: 'Born of the Gods Promos', code: 'PBNG' },
    { value: 'pjou', label: 'Journey into Nyx Promos', code: 'PJOU' },
    { value: 'pm14', label: 'Magic 2014 Promos', code: 'PM14' },
    { value: 'pm15', label: 'Magic 2015 Promos', code: 'PM15' },
    { value: 'pktk', label: 'Khans of Tarkir Promos', code: 'PKTK' },
    { value: 'pfrf', label: 'Fate Reforged Promos', code: 'PFRF' },
    { value: 'pdtk', label: 'Dragons of Tarkir Promos', code: 'PDTK' },
    { value: 'pori', label: 'Magic Origins Promos', code: 'PORI' },
    { value: 'pbfz', label: 'Battle for Zendikar Promos', code: 'PBFZ' },
    { value: 'pogw', label: 'Oath of the Gatewatch Promos', code: 'POGW' },
    { value: 'psoi', label: 'Shadows over Innistrad Promos', code: 'PSOI' },
    { value: 'pemn', label: 'Eldritch Moon Promos', code: 'PEMN' },
    { value: 'pkld', label: 'Kaladesh Promos', code: 'PKLD' },
    { value: 'paer', label: 'Aether Revolt Promos', code: 'PAER' },
    { value: 'pakh', label: 'Amonkhet Promos', code: 'PAKH' },
    { value: 'phou', label: 'Hour of Devastation Promos', code: 'PHOU' },
    { value: 'pxln', label: 'Ixalan Promos', code: 'PXLN' },
    { value: 'prix', label: 'Rivals of Ixalan Promos', code: 'PRIX' },
    { value: 'pdom', label: 'Dominaria Promos', code: 'PDOM' },
    { value: 'pm19', label: 'Core Set 2019 Promos', code: 'PM19' },
    { value: 'pgrn', label: 'Guilds of Ravnica Promos', code: 'PGRN' },
    { value: 'prna', label: 'Ravnica Allegiance Promos', code: 'PRNA' },
    { value: 'pwar', label: 'War of the Spark Promos', code: 'PWAR' },
    { value: 'pm20', label: 'Core Set 2020 Promos', code: 'PM20' },
    { value: 'peld', label: 'Throne of Eldraine Promos', code: 'PELD' },
    { value: 'pthb', label: 'Theros Beyond Death Promos', code: 'PTHB' },
    { value: 'piko', label: 'Ikoria: Lair of Behemoths Promos', code: 'PIKO' },
    { value: 'pm21', label: 'Core Set 2021 Promos', code: 'PM21' },
    { value: 'pznr', label: 'Zendikar Rising Promos', code: 'PZNR' },
    { value: 'pkhm', label: 'Kaldheim Promos', code: 'PKHM' },
    { value: 'pstx', label: 'Strixhaven Promos', code: 'PSTX' },
    { value: 'pafr', label: 'Adventures in the Forgotten Realms Promos', code: 'PAFR' },
    { value: 'pmid', label: 'Innistrad: Midnight Hunt Promos', code: 'PMID' },
    { value: 'pvow', label: 'Innistrad: Crimson Vow Promos', code: 'PVOW' },
    { value: 'pneo', label: 'Kamigawa: Neon Dynasty Promos', code: 'PNEO' },
    { value: 'psnc', label: 'Streets of New Capenna Promos', code: 'PSNC' },
    { value: 'pdmu', label: 'Dominaria United Promos', code: 'PDMU' },
    { value: 'pbro', label: 'The Brothers\' War Promos', code: 'PBRO' },
    { value: 'pone', label: 'Phyrexia: All Will Be One Promos', code: 'PONE' },
    { value: 'pmom', label: 'March of the Machine Promos', code: 'PMOM' },
    { value: 'pmat', label: 'March of the Machine: The Aftermath Promos', code: 'PMAT' },
    { value: 'pltr', label: 'The Lord of the Rings: Tales of Middle-earth Promos', code: 'PLTR' },
    { value: 'pwoe', label: 'Wilds of Eldraine Promos', code: 'PWOE' },
    { value: 'plci', label: 'The Lost Caverns of Ixalan Promos', code: 'PLCI' },
    { value: 'pmkm', label: 'Murders at Karlov Manor Promos', code: 'PMKM' },
    { value: 'potj', label: 'Outlaws of Thunder Junction Promos', code: 'POTJ' },
    { value: 'pmh3', label: 'Modern Horizons 3 Promos', code: 'PMH3' },
    { value: 'pblb', label: 'Bloomburrow Promos', code: 'PBLB' },
    { value: 'pdsk', label: 'Duskmourn: House of Horror Promos', code: 'PDSK' },
    { value: 'pfdn', label: 'Foundations Promos', code: 'PFDN' },
    { value: 'dbl', label: 'Double Masters', code: 'DBL' },
    { value: '2x2', label: 'Double Masters 2022', code: '2X2' },
    { value: '2xm', label: 'Double Masters 2020', code: '2XM' },
    { value: 'ima', label: 'Iconic Masters', code: 'IMA' },
    { value: 'a25', label: 'Masters 25', code: 'A25' },
    { value: 'tpr', label: 'Tempest Remastered', code: 'TPR' },
    { value: 'vma', label: 'Vintage Masters', code: 'VMA' },
    { value: 'mma', label: 'Modern Masters', code: 'MMA' },
    { value: 'mm2', label: 'Modern Masters 2015', code: 'MM2' },
    { value: 'mm3', label: 'Modern Masters 2017', code: 'MM3' },
    { value: 'ddl', label: 'Duel Decks: Heroes vs. Monsters', code: 'DDL' },
    { value: 'ddm', label: 'Duel Decks: Jace vs. Vraska', code: 'DDM' },
    { value: 'ddn', label: 'Duel Decks: Speed vs. Cunning', code: 'DDN' },
    { value: 'ddo', label: 'Duel Decks: Elspeth vs. Kiora', code: 'DDO' },
    { value: 'ddp', label: 'Duel Decks: Zendikar vs. Eldrazi', code: 'DDP' },
    { value: 'ddq', label: 'Duel Decks: Blessed vs. Cursed', code: 'DDQ' },
    { value: 'ddr', label: 'Duel Decks: Nissa vs. Ob Nixilis', code: 'DDR' },
    { value: 'dds', label: 'Duel Decks: Mind vs. Might', code: 'DDS' },
    { value: 'ddt', label: 'Duel Decks: Merfolk vs. Goblins', code: 'DDT' },
    { value: 'ddu', label: 'Duel Decks: Elves vs. Inventors', code: 'DDU' },
    { value: 'gs2', label: 'Game Night 2019', code: 'GS2' },
    { value: 'tb', label: 'Battlebond', code: 'TB' },
    { value: 'cons', label: 'Conspiracy', code: 'CONS' },
    { value: 'cn2', label: 'Conspiracy: Take the Crown', code: 'CN2' },
    { value: 'ust', label: 'Unstable', code: 'UST' },
    { value: 'unf', label: 'Unfinity', code: 'UNF' },
    { value: 'und', label: 'Undaunted', code: 'UND' },
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
    { value: 'fdn', label: 'Foundations', code: 'FDN' }
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

// Format date and time for display
function formatDateTime(dateString) {
    if (!dateString) return 'Unknown';
    
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
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
function createEnhancedCardDetailHTML(card, filteredCards) {
    // DEBUG: Log card data for magnifying glass debugging
    console.log('🔍 DEBUG: Card data for magnifying glass:', {
        name: card.name,
        added_method: card.added_method,
        scan_id: card.scan_id,
        id: card.id,
        condition: card.added_method === 'SCANNED' && card.scan_id && card.id
    });
    
    const condition = card.condition && CONDITION_OPTIONS.find(opt => opt.value === card.condition) ? card.condition : 'LP';
    const conditionLabel = CONDITION_OPTIONS.find(opt => opt.value === condition)?.label || 'Lightly Played';
    const conditionDisplay = `<span class="read-only-field">${conditionLabel}</span>`;
    
    const rarity = card.rarity && RARITY_OPTIONS.find(opt => opt.value === card.rarity.toLowerCase()) ? card.rarity.toLowerCase() : 'unknown';
    const rarityLabel = RARITY_OPTIONS.find(opt => opt.value === rarity)?.label || 'Unknown';
    const rarityDisplay = `<span class="read-only-field">${rarityLabel}</span>`;
    
    const setCode = card.set_code ? card.set_code.toLowerCase() : 'unknown';
    const setLabel = SET_OPTIONS.find(opt => opt.value === setCode)?.label || card.set_name || 'Unknown Set';
    const setDisplay = `<span class="read-only-field">${setLabel}</span>`;
    
    // Calculate the correct count to display - always show actual database count
    let displayCount;
    if (card.total_cards) {
        // In stacked view, total_cards represents the number of duplicate entries
        displayCount = card.total_cards;
    } else if (card.stack_count) {
        // Use stack_count if available
        displayCount = card.stack_count;
    } else {
        // Fallback to individual count
        displayCount = card.count || 1;
    }
    
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
                    <span class="detail-label">ID:</span>
                    <span class="detail-value">${card.unique_id || card.id || 'N/A'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Set:</span>
                    <span class="detail-value">${setDisplay}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Rarity:</span>
                    <span class="detail-value">${rarityDisplay}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Mana Cost:</span>
                    <span class="detail-value mana-cost-display">${formatManaCost(card.mana_cost)}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Count:</span>
                    <span class="detail-value">${displayCount}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Condition:</span>
                    <span class="detail-value">${conditionDisplay}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Added:</span>
                    <span class="detail-value">
                        ${formatDateTime(card.first_seen)} 
                        <span class="added-method">(${formatAddedMethod(card.added_method)}${card.added_method === 'SCANNED' && card.scan_id && card.id ? `<button class="scan-emoji-btn" onclick="viewCardScanImage(${card.id}, &quot;${card.name.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')}&quot;)" title="View specific scan image that produced this card" style="background: none; border: none; cursor: pointer; font-size: 1.2rem; color: #4fc3f7; padding: 0 2px; border-radius: 50%; vertical-align: middle; margin-left: 2px;">🔍</button>` : ''})</span>
                        <!-- DEBUG: added_method=${card.added_method}, scan_id=${card.scan_id}, id=${card.id} -->
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Last Updated:</span>
                    <span class="detail-value">
                        ${formatDateTime(card.last_seen)}
                    </span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Prices:</span>
                    <div class="price-details" data-base-price-usd="${card.price_usd || 0}" data-base-price-eur="${card.price_eur || 0}">
                        <span class="price-item price-usd" id="modalPriceUSD">$${getConditionAdjustedPrice(card.price_usd || 0, card.condition).toFixed(2)}</span>
                        <span class="price-item price-eur" id="modalPriceEUR">€${getConditionAdjustedPrice(card.price_eur || 0, card.condition).toFixed(2)}</span>
                        <span class="condition-note" id="modalConditionNote">${card.condition !== 'NM' ? `(${card.condition} condition)` : ''}</span>
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
    `;
}

// Update modal price display immediately when condition changes
function updateModalPriceDisplay(newCondition) {
    const priceDetails = document.querySelector('.price-details');
    const priceUSD = document.getElementById('modalPriceUSD');
    const priceEUR = document.getElementById('modalPriceEUR');
    const conditionNote = document.getElementById('modalConditionNote');
    
    if (priceDetails && priceUSD && priceEUR && conditionNote) {
        const basePriceUSD = parseFloat(priceDetails.dataset.basePriceUsd) || 0;
        const basePriceEUR = parseFloat(priceDetails.dataset.basePriceEur) || 0;
        
        const adjustedPriceUSD = getConditionAdjustedPrice(basePriceUSD, newCondition);
        const adjustedPriceEUR = getConditionAdjustedPrice(basePriceEUR, newCondition);
        
        priceUSD.textContent = `$${adjustedPriceUSD.toFixed(2)}`;
        priceEUR.textContent = `€${adjustedPriceEUR.toFixed(2)}`;
        conditionNote.textContent = newCondition !== 'NM' ? `(${newCondition} condition)` : '';
    }
}

// Update card condition with live price update
async function updateCardConditionWithLivePrice(cardId, newCondition) {
    // Update price display immediately for instant feedback
    updateModalPriceDisplay(newCondition);
    
    // Then update via API
    await updateCardCondition(cardId, newCondition);
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
            await loadStats();
        } else {
            alert('Failed to update card condition.');
        }
    } catch (error) {
        console.error('Error updating card condition:', error);
        alert('Error updating card condition.');
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
            await loadStats();
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
                    const responseClone = response.clone();
                    const errorData = await responseClone.json();
                    errorMessage = errorData.detail || errorData.error || errorMessage;
                } catch (e) {
                    try {
                    const errorText = await response.text();
                    errorMessage = errorText || errorMessage;
                    } catch (textError) {
                        // If both JSON and text parsing fail, use default message
                        errorMessage = 'Failed to start processing';
                    }
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
                    <button class="scan-retry-btn" onclick="retryScan()">
                        <i class="fas fa-redo"></i> Retry
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
                <button class="scan-accept-all-btn" onclick="acceptAllResults()">
                    <i class="fas fa-check-circle"></i> Accept All
                </button>
                <button class="scan-reject-all-btn" onclick="rejectAllResults()">
                    <i class="fas fa-times-circle"></i> Reject All
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

// Create set display for scan result with unknown set detection
function createSetDisplayForScanResult(result) {
    const setName = result.set_name || '';
    const setCode = result.set_code || '';
    
    // Check if set is unknown/missing
    const isUnknownSet = !setName || 
                        setName.toLowerCase().includes('unknown') || 
                        setName.toLowerCase().includes('not found') ||
                        setCode.toLowerCase().includes('unknown') ||
                        setCode === '' ||
                        setName === 'Unknown Set';
    
    if (isUnknownSet) {
        return `
            <div class="scan-result-set unknown-set">
                <div class="unknown-set-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span>Unknown Set - Please Select:</span>
                </div>
                <div class="set-correction-container">
                    <select class="set-correction-dropdown" 
                            onchange="updateScanResultSet(${result.id}, this.value)"
                            data-result-id="${result.id}">
                        <option value="">Select Set...</option>
                        <option value="m21|Core Set 2021">Core Set 2021 (M21)</option>
                        <option value="znr|Zendikar Rising">Zendikar Rising (ZNR)</option>
                        <option value="khm|Kaldheim">Kaldheim (KHM)</option>
                        <option value="stx|Strixhaven">Strixhaven (STX)</option>
                        <option value="afr|Adventures in the Forgotten Realms">Adventures in the Forgotten Realms (AFR)</option>
                        <option value="mid|Innistrad: Midnight Hunt">Innistrad: Midnight Hunt (MID)</option>
                        <option value="vow|Innistrad: Crimson Vow">Innistrad: Crimson Vow (VOW)</option>
                        <option value="neo|Kamigawa: Neon Dynasty">Kamigawa: Neon Dynasty (NEO)</option>
                        <option value="snc|Streets of New Capenna">Streets of New Capenna (SNC)</option>
                        <option value="clb|Commander Legends: Battle for Baldur's Gate">Commander Legends: Battle for Baldur's Gate (CLB)</option>
                        <option value="2x2|Double Masters 2022">Double Masters 2022 (2X2)</option>
                        <option value="dmu|Dominaria United">Dominaria United (DMU)</option>
                        <option value="bro|The Brothers' War">The Brothers' War (BRO)</option>
                        <option value="one|Phyrexia: All Will Be One">Phyrexia: All Will Be One (ONE)</option>
                        <option value="mom|March of the Machine">March of the Machine (MOM)</option>
                        <option value="mat|March of the Machine: The Aftermath">March of the Machine: The Aftermath (MAT)</option>
                        <option value="ltr|The Lord of the Rings: Tales of Middle-earth">The Lord of the Rings: Tales of Middle-earth (LTR)</option>
                        <option value="woe|Wilds of Eldraine">Wilds of Eldraine (WOE)</option>
                        <option value="lci|The Lost Caverns of Ixalan">The Lost Caverns of Ixalan (LCI)</option>
                        <option value="mkm|Murders at Karlov Manor">Murders at Karlov Manor (MKM)</option>
                        <option value="otj|Outlaws of Thunder Junction">Outlaws of Thunder Junction (OTJ)</option>
                        <option value="mh3|Modern Horizons 3">Modern Horizons 3 (MH3)</option>
                        <option value="blb|Bloomburrow">Bloomburrow (BLB)</option>
                        <option value="dsk|Duskmourn: House of Horror">Duskmourn: House of Horror (DSK)</option>
                        <option value="fdn|Foundations">Foundations (FDN)</option>
                        <option value="other|Other (specify manually)">Other (specify manually)</option>
                    </select>
                    <button class="set-search-btn" onclick="showSetSearchForResult(${result.id})" title="Search for set">
                        <i class="fas fa-search"></i>
                    </button>
                </div>
            </div>
        `;
    } else {
        return `<div class="scan-result-set">${setName}</div>`;
    }
}

// Update scan result set when selected from dropdown
async function updateScanResultSet(resultId, setSelection) {
    if (!setSelection) return;
    
    try {
        const [setCode, setName] = setSelection.split('|');
        
        if (setSelection === 'other') {
            // Show manual entry for other sets
            showSetSearchForResult(resultId);
            return;
        }
        
        // Update the scan result in the backend
        const response = await fetch(`/scan/result/${resultId}/set`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                set_code: setCode,
                set_name: setName
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update set information');
        }
        
        // Update the UI to show the new set
        const resultElement = document.querySelector(`[data-result-id="${resultId}"]`);
        const setContainer = resultElement.querySelector('.scan-result-set');
        setContainer.outerHTML = `<div class="scan-result-set">${setName}</div>`;
        
        console.log(`Updated scan result ${resultId} set to: ${setName} (${setCode})`);
        
    } catch (error) {
        console.error('Error updating scan result set:', error);
        alert('Failed to update set information');
    }
}

// Show set search modal for manual entry
function showSetSearchForResult(resultId) {
    // Store the result ID for later use
    window.currentSetSearchResultId = resultId;
    
    // Create and show set search modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'setSearchModal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Search for Card Set</h3>
                <button class="close-btn" onclick="closeSetSearchModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="set-search-container">
                    <input type="text" id="setSearchInput" placeholder="Enter set name or code..." 
                           onkeyup="searchSets(this.value)" autocomplete="off">
                    <div id="setSearchResults" class="set-search-results">
                        <div class="search-instruction">Start typing to search for Magic sets...</div>
                    </div>
                </div>
                <div class="manual-entry-container">
                    <h4>Or Enter Manually:</h4>
                    <div class="manual-entry-form">
                        <input type="text" id="manualSetCode" placeholder="Set Code (e.g., ZNR)" maxlength="10">
                        <input type="text" id="manualSetName" placeholder="Set Name (e.g., Zendikar Rising)">
                        <button onclick="applyManualSet()" class="apply-set-btn">Apply Set</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
    
    // Focus on search input
    setTimeout(() => {
        document.getElementById('setSearchInput').focus();
    }, 100);
}

// Close set search modal
function closeSetSearchModal() {
    const modal = document.getElementById('setSearchModal');
    if (modal) {
        modal.remove();
    }
    window.currentSetSearchResultId = null;
}

// Search for sets (simplified version - in practice you might want to use Scryfall API)
function searchSets(query) {
    const resultsContainer = document.getElementById('setSearchResults');
    
    if (!query || query.length < 2) {
        resultsContainer.innerHTML = '<div class="search-instruction">Start typing to search for Magic sets...</div>';
        return;
    }
    
    // Simplified set list for searching
    const commonSets = [
        { code: 'FDN', name: 'Foundations' },
        { code: 'DSK', name: 'Duskmourn: House of Horror' },
        { code: 'BLB', name: 'Bloomburrow' },
        { code: 'MH3', name: 'Modern Horizons 3' },
        { code: 'OTJ', name: 'Outlaws of Thunder Junction' },
        { code: 'MKM', name: 'Murders at Karlov Manor' },
        { code: 'LCI', name: 'The Lost Caverns of Ixalan' },
        { code: 'WOE', name: 'Wilds of Eldraine' },
        { code: 'LTR', name: 'The Lord of the Rings: Tales of Middle-earth' },
        { code: 'MAT', name: 'March of the Machine: The Aftermath' },
        { code: 'MOM', name: 'March of the Machine' },
        { code: 'ONE', name: 'Phyrexia: All Will Be One' },
        { code: 'BRO', name: 'The Brothers\' War' },
        { code: 'DMU', name: 'Dominaria United' },
        { code: '2X2', name: 'Double Masters 2022' },
        { code: 'CLB', name: 'Commander Legends: Battle for Baldur\'s Gate' },
        { code: 'SNC', name: 'Streets of New Capenna' },
        { code: 'NEO', name: 'Kamigawa: Neon Dynasty' },
        { code: 'VOW', name: 'Innistrad: Crimson Vow' },
        { code: 'MID', name: 'Innistrad: Midnight Hunt' },
        { code: 'AFR', name: 'Adventures in the Forgotten Realms' },
        { code: 'STX', name: 'Strixhaven: School of Mages' },
        { code: 'KHM', name: 'Kaldheim' },
        { code: 'ZNR', name: 'Zendikar Rising' },
        { code: 'M21', name: 'Core Set 2021' },
        { code: 'IKO', name: 'Ikoria: Lair of Behemoths' },
        { code: 'THB', name: 'Theros Beyond Death' },
        { code: 'ELD', name: 'Throne of Eldraine' },
        { code: 'M20', name: 'Core Set 2020' },
        { code: 'WAR', name: 'War of the Spark' },
        { code: 'RNA', name: 'Ravnica Allegiance' },
        { code: 'GRN', name: 'Guilds of Ravnica' },
        { code: 'M19', name: 'Core Set 2019' },
        { code: 'DOM', name: 'Dominaria' },
        { code: 'RIX', name: 'Rivals of Ixalan' },
        { code: 'XLN', name: 'Ixalan' }
    ];
    
    const filteredSets = commonSets.filter(set => 
        set.name.toLowerCase().includes(query.toLowerCase()) ||
        set.code.toLowerCase().includes(query.toLowerCase())
    );
    
    if (filteredSets.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No sets found. Try a different search term.</div>';
        return;
    }
    
    const resultsHtml = filteredSets.map(set => `
        <div class="set-search-result" onclick="selectSearchedSet('${set.code}', '${set.name}')">
            <div class="set-code">${set.code}</div>
            <div class="set-name">${set.name}</div>
        </div>
    `).join('');
    
    resultsContainer.innerHTML = resultsHtml;
}

// Select a set from search results
async function selectSearchedSet(setCode, setName) {
    const resultId = window.currentSetSearchResultId;
    if (!resultId) return;
    
    try {
        await updateScanResultSet(resultId, `${setCode}|${setName}`);
        closeSetSearchModal();
    } catch (error) {
        console.error('Error selecting searched set:', error);
    }
}

// Apply manually entered set
async function applyManualSet() {
    const setCode = document.getElementById('manualSetCode').value.trim();
    const setName = document.getElementById('manualSetName').value.trim();
    const resultId = window.currentSetSearchResultId;
    
    if (!setCode || !setName || !resultId) {
        alert('Please enter both set code and set name');
        return;
    }
    
    try {
        await updateScanResultSet(resultId, `${setCode}|${setName}`);
        closeSetSearchModal();
    } catch (error) {
        console.error('Error applying manual set:', error);
    }
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
                ${createSetDisplayForScanResult(result)}
                <span class="confidence-score ${confidenceClass}">
                    ${Math.round(result.confidence_score)}% confidence
                </span>
                ${result.requires_review ? '<span class="review-warning">⚠ Needs review</span>' : ''}
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
                <button class="scan-action-btn info" 
                        onclick="showAIResponse(${currentScan.id})" 
                        title="Show AI Response Details">
                    <i class="fas fa-info-circle"></i> INFO
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

// Retry scan
async function retryScan() {
    if (!currentScan || !currentScan.id) {
        alert('No scan to retry');
        return;
    }
    
    try {
        // Get the current scan files
        const scanFiles = currentScan.files || [];
        
        if (scanFiles.length === 0) {
            alert('No scan files available to retry');
            return;
        }
        
        // Clear current scan polling
        if (scanPollingInterval) {
            clearInterval(scanPollingInterval);
            scanPollingInterval = null;
        }
        
        // Start a new scan with the same files
        const scanResult = await uploadAndScan(scanFiles);
        
        if (scanResult.success) {
            // Update current scan reference
            currentScan.id = scanResult.scan_id;
            
            // Restart the scanning workflow
            await showScanningModal(scanResult.scan_id, scanFiles);
        } else {
            alert(`Error retrying scan: ${scanResult.error}`);
        }
        
    } catch (error) {
        console.error('Error retrying scan:', error);
        alert('Error retrying scan. Please try again.');
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
                
                // Calculate new translate to zoom towards cursor
                const newTranslateX = translateX * (newScale / scale) - cursorX * (newScale / scale - 1);
                const newTranslateY = translateY * (newScale / scale) - cursorY * (newScale / scale - 1);
                
                scale = newScale;
                translateX = newTranslateX;
                translateY = newTranslateY;
                
                scanImage.style.transform = `scale(${scale}) translate(${translateX}px, ${translateY}px)`;
            }, { passive: false });
            
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
                    <img src="/uploads/${fileName}" alt="${fileName}" class="full-scan-image">
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
            
            // Calculate new translate to zoom towards cursor
            const newTranslateX = translateX * (newScale / scale) - cursorX * (newScale / scale - 1);
            const newTranslateY = translateY * (newScale / scale) - cursorY * (newScale / scale - 1);
            
            scale = newScale;
            translateX = newTranslateX;
            translateY = newTranslateY;
            
            scanImage.style.transform = `scale(${scale}) translate(${translateX}px, ${translateY}px)`;
        }, { passive: false });
        
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

// Sort dropdown functionality
function toggleSortMenu() {
    const dropdown = document.getElementById('sortDropdown');
    dropdown.classList.toggle('show');
}

// Close sort dropdown when clicking outside
document.addEventListener('click', function(event) {
    const sortContainer = document.querySelector('.sort-container');
    const dropdown = document.getElementById('sortDropdown');
    
    if (dropdown && !sortContainer.contains(event.target)) {
        dropdown.classList.remove('show');
    }
});

// Toggle sort direction
function toggleSortDirection() {
    sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    updateSortDirectionIcon();
    displayCards(); // Refresh the display
}

// Update sort direction icon
function updateSortDirectionIcon() {
    const icon = document.getElementById('sortDirectionIcon');
    if (!icon) return;
    
    if (sortDirection === 'asc') {
        icon.className = 'fas fa-sort-alpha-down';
    } else {
        icon.className = 'fas fa-sort-alpha-up';
    }
}

// Set sort field
function setSortField(field) {
    // Remove active class from all sort items
    document.querySelectorAll('.sort-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Add active class to selected item
    const selectedItem = document.querySelector(`[data-field="${field}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
    
    // Update sort field
    sortField = field;
    
    // Update direction icon based on field type
    updateSortDirectionIcon();
    
    // Close dropdown
    const dropdown = document.getElementById('sortDropdown');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    
    // Refresh display
    displayCards();
}

// Initialize sort UI
function initializeSortUI() {
    // Set initial active sort item
    const nameItem = document.querySelector('[data-field="name"]');
    if (nameItem) {
        nameItem.classList.add('active');
    }
    
    // Set initial sort direction icon
    updateSortDirectionIcon();
}

// View scan image functionality
async function viewScanImage(scanId, cardName) {
    try {
        // Fetch scan data to get the image filename
        const response = await fetch(`/scan/${scanId}/details`);
        if (!response.ok) {
            throw new Error('Failed to fetch scan details');
        }
        
        const scanData = await response.json();
        if (!scanData.success || !scanData.scan.images || scanData.scan.images.length === 0) {
            alert('No scan image found for this card');
            return;
        }
        
        // Use the first image from the scan
        const imageFilename = scanData.scan.images[0].filename;
        const imageUrl = `/uploads/${imageFilename}`;
        
        // Show the scan image in full screen
        showFullScanImage(imageFilename, imageUrl, `Original scan for: ${cardName}`);
        
    } catch (error) {
        console.error('Error viewing scan image:', error);
        alert('Failed to load scan image');
    }
}


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
    
    // Create summary section
    const summaryHtml = scanHistory.summary ? `
        <div class="scan-history-summary">
            <h3><i class="fas fa-chart-pie"></i> Scan Summary</h3>
            <div class="summary-stats">
                <div class="summary-stat">
                    <span class="stat-number">${scanHistory.summary.scans_with_cards}</span>
                    <span class="stat-label">Successful Scans</span>
                </div>
                <div class="summary-stat">
                    <span class="stat-number">${scanHistory.summary.total_images}</span>
                    <span class="stat-label">Total Images</span>
                </div>
                <div class="summary-stat">
                    <span class="stat-number">${scanHistory.summary.total_cards}</span>
                    <span class="stat-label">Cards Found</span>
                </div>
            </div>
        </div>
    ` : '';
    
    body.innerHTML = `
        ${summaryHtml}
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
                 loading="lazy"
                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiIGZpbGw9IiNFRUVFRUUiLz48dGV4dCB4PSI1MCIgeT0iNTUiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiM5OTkiIHRleHQtYW5jaG9yPSJtaWRkbGUiPk5vIEltYWdlPC90ZXh0Pjwvc3ZnPg=='; this.onerror=null; this.alt='Image not available';"
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
    
    return `
        <div class="scan-item">
            <div class="scan-header">
                <div class="scan-info">
                    <h4>Scan #${scan.id}</h4>
                    <div class="scan-meta">
                        ${formattedDate} at ${formattedTime}
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

// Unknown Sets Review functionality
async function showUnknownSetsReview() {
    // Close tools dropdown
    const dropdown = document.getElementById('toolsDropdown');
    dropdown.classList.remove('show');
    
    // Show modal
    const modal = document.getElementById('unknownSetsModal');
    modal.style.display = 'flex';
    
    // Load unknown sets data
    await loadUnknownSetsData();
}

// Close unknown sets review modal
function closeUnknownSetsModal() {
    const modal = document.getElementById('unknownSetsModal');
    modal.style.display = 'none';
    
    // Clear current review state
    window.currentUnknownSetsReview = null;
}

// Load cards with unknown sets
async function loadUnknownSetsData() {
    try {
        const response = await fetch('/cards/unknown-sets');
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Failed to load unknown sets data');
        }
        
        displayUnknownSetsReview(data.cards);
        
    } catch (error) {
        console.error('Error loading unknown sets:', error);
        const body = document.getElementById('unknownSetsBody');
        body.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Failed to load cards with unknown sets</p>
                <button onclick="loadUnknownSetsData()" class="retry-btn">Retry</button>
            </div>
        `;
    }
}

// Display unknown sets review interface
function displayUnknownSetsReview(cards) {
    const body = document.getElementById('unknownSetsBody');
    
    if (!cards || cards.length === 0) {
        body.innerHTML = `
            <div class="no-unknown-sets">
                <i class="fas fa-check-circle"></i>
                <h3>No Unknown Sets Found!</h3>
                <p>All cards in your collection have proper set information.</p>
            </div>
        `;
        return;
    }
    
    // Initialize review state
    window.currentUnknownSetsReview = {
        cards: cards,
        currentIndex: 0,
        totalCards: cards.length
    };
    
    // Show the first card
    showUnknownSetCard(0);
}

// Show a specific unknown set card for review
function showUnknownSetCard(index) {
    const review = window.currentUnknownSetsReview;
    if (!review || index < 0 || index >= review.totalCards) return;
    
    review.currentIndex = index;
    const card = review.cards[index];
    const body = document.getElementById('unknownSetsBody');
    
    body.innerHTML = `
        <div class="unknown-set-review-container">
            <div class="review-header">
                <div class="review-progress">
                    Card ${index + 1} of ${review.totalCards}
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${((index + 1) / review.totalCards) * 100}%"></div>
                    </div>
                </div>
            </div>
            
            <div class="review-card-display">
                <div class="review-card-image">
                    <img src="${card.image_url || 'https://via.placeholder.com/200x279/667eea/ffffff?text=No+Image'}" 
                         alt="${card.name}" 
                         onerror="this.src='https://via.placeholder.com/200x279/667eea/ffffff?text=No+Image'">
                    ${card.scan_id ? `<button class="view-scan-btn-review" onclick="viewScanImage(${card.scan_id}, '${card.name}')" title="View scanned image">👓</button>` : ''}
                    <div class="rescan-button-container">
                        ${card.scan_id ? `<button class="rescan-btn" onclick="rescanCard(${card.scan_id})" title="Rescan this image">
                            <i class="fas fa-redo"></i> RESCAN
                        </button>` : ''}
                    </div>
                </div>
                
                <div class="review-card-info">
                    <h4>${card.name}</h4>
                    <div class="current-set-info">
                        <p><strong>Current Set:</strong> <span class="unknown-indicator">${card.set_name || 'Unknown'}</span></p>
                        <p><strong>Set Code:</strong> <span class="unknown-indicator">${card.set_code || 'Unknown'}</span></p>
                        <p><strong>Added:</strong> ${formatDateTime(card.first_seen)} (${formatAddedMethod(card.added_method)})</p>
                    </div>
                    
                    <div class="set-correction-section">
                        <h5>Select Correct Set:</h5>
                        <div class="set-selection-container">
                            <select class="review-set-dropdown" id="reviewSetDropdown">
                                <option value="">Select Set...</option>
                                <option value="m21|Core Set 2021">Core Set 2021 (M21)</option>
                                <option value="znr|Zendikar Rising">Zendikar Rising (ZNR)</option>
                                <option value="khm|Kaldheim">Kaldheim (KHM)</option>
                                <option value="stx|Strixhaven">Strixhaven (STX)</option>
                                <option value="afr|Adventures in the Forgotten Realms">Adventures in the Forgotten Realms (AFR)</option>
                                <option value="mid|Innistrad: Midnight Hunt">Innistrad: Midnight Hunt (MID)</option>
                                <option value="vow|Innistrad: Crimson Vow">Innistrad: Crimson Vow (VOW)</option>
                                <option value="neo|Kamigawa: Neon Dynasty">Kamigawa: Neon Dynasty (NEO)</option>
                                <option value="snc|Streets of New Capenna">Streets of New Capenna (SNC)</option>
                                <option value="clb|Commander Legends: Battle for Baldur's Gate">Commander Legends: Battle for Baldur's Gate (CLB)</option>
                                <option value="2x2|Double Masters 2022">Double Masters 2022 (2X2)</option>
                                <option value="dmu|Dominaria United">Dominaria United (DMU)</option>
                                <option value="bro|The Brothers' War">The Brothers' War (BRO)</option>
                                <option value="one|Phyrexia: All Will Be One">Phyrexia: All Will Be One (ONE)</option>
                                <option value="mom|March of the Machine">March of the Machine (MOM)</option>
                                <option value="mat|March of the Machine: The Aftermath">March of the Machine: The Aftermath (MAT)</option>
                                <option value="ltr|The Lord of the Rings: Tales of Middle-earth">The Lord of the Rings: Tales of Middle-earth (LTR)</option>
                                <option value="woe|Wilds of Eldraine">Wilds of Eldraine (WOE)</option>
                                <option value="lci|The Lost Caverns of Ixalan">The Lost Caverns of Ixalan (LCI)</option>
                                <option value="mkm|Murders at Karlov Manor">Murders at Karlov Manor (MKM)</option>
                                <option value="otj|Outlaws of Thunder Junction">Outlaws of Thunder Junction (OTJ)</option>
                                <option value="mh3|Modern Horizons 3">Modern Horizons 3 (MH3)</option>
                                <option value="blb|Bloomburrow">Bloomburrow (BLB)</option>
                                <option value="dsk|Duskmourn: House of Horror">Duskmourn: House of Horror (DSK)</option>
                                <option value="fdn|Foundations">Foundations (FDN)</option>
                                <option value="other|Other (specify manually)">Other (specify manually)</option>
                            </select>
                            <button onclick="showSetSearchForCard(${card.id})" class="search-set-btn">
                                <i class="fas fa-search"></i> Search
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="review-actions">
                <div class="navigation-buttons">
                    <button onclick="navigateUnknownSet(-1)" ${index === 0 ? 'disabled' : ''} class="nav-btn">
                        <i class="fas fa-chevron-left"></i> Previous
                    </button>
                    <button onclick="skipUnknownSetCard()" class="skip-btn">
                        <i class="fas fa-forward"></i> Skip
                    </button>
                    <button onclick="navigateUnknownSet(1)" ${index === review.totalCards - 1 ? 'disabled' : ''} class="nav-btn">
                        Next <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                
                <div class="action-buttons">
                    <button onclick="applySetToCard()" class="apply-btn" id="applySetBtn" disabled>
                        <i class="fas fa-check"></i> Apply Set
                    </button>
                    <button onclick="closeUnknownSetsModal()" class="close-review-btn">
                        <i class="fas fa-times"></i> Close Review
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Set up dropdown change handler
    const dropdown = document.getElementById('reviewSetDropdown');
    dropdown.addEventListener('change', function() {
        const applyBtn = document.getElementById('applySetBtn');
        applyBtn.disabled = !this.value;
    });
}

// Navigate between unknown set cards
function navigateUnknownSet(direction) {
    const review = window.currentUnknownSetsReview;
    if (!review) return;
    
    const newIndex = review.currentIndex + direction;
    if (newIndex >= 0 && newIndex < review.totalCards) {
        showUnknownSetCard(newIndex);
    }
}

// Skip current unknown set card
function skipUnknownSetCard() {
    const review = window.currentUnknownSetsReview;
    if (!review) return;
    
    if (review.currentIndex < review.totalCards - 1) {
        navigateUnknownSet(1);
    } else {
        // Last card, close review
        closeUnknownSetsModal();
    }
}

// Apply selected set to current card
async function applySetToCard() {
    const review = window.currentUnknownSetsReview;
    if (!review) return;
    
    const dropdown = document.getElementById('reviewSetDropdown');
    const setSelection = dropdown.value;
    
    if (!setSelection) {
        alert('Please select a set first');
        return;
    }
    
    if (setSelection === 'other') {
        showSetSearchForCard(review.cards[review.currentIndex].id);
        return;
    }
    
    const [setCode, setName] = setSelection.split('|');
    const cardId = review.cards[review.currentIndex].id;
    
    try {
        const response = await fetch(`/cards/${cardId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                set_code: setCode,
                set_name: setName
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update card set');
        }
        
        // Remove this card from the review list
        review.cards.splice(review.currentIndex, 1);
        review.totalCards--;
        
        // Show next card or close if done
        if (review.totalCards === 0) {
            displayUnknownSetsReview([]);
        } else if (review.currentIndex >= review.totalCards) {
            showUnknownSetCard(review.totalCards - 1);
        } else {
            showUnknownSetCard(review.currentIndex);
        }
        
        console.log(`Updated card ${cardId} set to: ${setName} (${setCode})`);
        
    } catch (error) {
        console.error('Error updating card set:', error);
        alert('Failed to update card set');
    }
}

// Show set search for a specific card
function showSetSearchForCard(cardId) {
    window.currentSetSearchCardId = cardId;
    showSetSearchModal();
}

// Modified set search modal for card review
function showSetSearchModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'setSearchModalReview';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>Search for Card Set</h3>
                <button class="close-btn" onclick="closeSetSearchModalReview()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="set-search-container">
                    <input type="text" id="setSearchInputReview" placeholder="Enter set name or code..." 
                           onkeyup="searchSetsReview(this.value)" autocomplete="off">
                    <div id="setSearchResultsReview" class="set-search-results">
                        <div class="search-instruction">Start typing to search for Magic sets...</div>
                    </div>
                </div>
                <div class="manual-entry-container">
                    <h4>Or Enter Manually:</h4>
                    <div class="manual-entry-form">
                        <input type="text" id="manualSetCodeReview" placeholder="Set Code (e.g., ZNR)" maxlength="10">
                        <input type="text" id="manualSetNameReview" placeholder="Set Name (e.g., Zendikar Rising)">
                        <button onclick="applyManualSetReview()" class="apply-set-btn">Apply Set</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
    
    setTimeout(() => {
        document.getElementById('setSearchInputReview').focus();
    }, 100);
}

function closeSetSearchModalReview() {
    const modal = document.getElementById('setSearchModalReview');
    if (modal) {
        modal.remove();
    }
    window.currentSetSearchCardId = null;
}

function searchSetsReview(query) {
    // Reuse the same search logic but with different element IDs
    const resultsContainer = document.getElementById('setSearchResultsReview');
    
    if (!query || query.length < 2) {
        resultsContainer.innerHTML = '<div class="search-instruction">Start typing to search for Magic sets...</div>';
        return;
    }
    
    // Same sets list as before
    const commonSets = [
        { code: 'FDN', name: 'Foundations' },
        { code: 'DSK', name: 'Duskmourn: House of Horror' },
        { code: 'BLB', name: 'Bloomburrow' },
        { code: 'MH3', name: 'Modern Horizons 3' },
        { code: 'OTJ', name: 'Outlaws of Thunder Junction' },
        { code: 'MKM', name: 'Murders at Karlov Manor' },
        { code: 'LCI', name: 'The Lost Caverns of Ixalan' },
        { code: 'WOE', name: 'Wilds of Eldraine' },
        { code: 'LTR', name: 'The Lord of the Rings: Tales of Middle-earth' },
        { code: 'MAT', name: 'March of the Machine: The Aftermath' },
        { code: 'MOM', name: 'March of the Machine' },
        { code: 'ONE', name: 'Phyrexia: All Will Be One' },
        { code: 'BRO', name: 'The Brothers\' War' },
        { code: 'DMU', name: 'Dominaria United' },
        { code: '2X2', name: 'Double Masters 2022' },
        { code: 'CLB', name: 'Commander Legends: Battle for Baldur\'s Gate' },
        { code: 'SNC', name: 'Streets of New Capenna' },
        { code: 'NEO', name: 'Kamigawa: Neon Dynasty' },
        { code: 'VOW', name: 'Innistrad: Crimson Vow' },
        { code: 'MID', name: 'Innistrad: Midnight Hunt' },
        { code: 'AFR', name: 'Adventures in the Forgotten Realms' },
        { code: 'STX', name: 'Strixhaven: School of Mages' },
        { code: 'KHM', name: 'Kaldheim' },
        { code: 'ZNR', name: 'Zendikar Rising' },
        { code: 'M21', name: 'Core Set 2021' },
        { code: 'IKO', name: 'Ikoria: Lair of Behemoths' },
        { code: 'THB', name: 'Theros Beyond Death' },
        { code: 'ELD', name: 'Throne of Eldraine' },
        { code: 'M20', name: 'Core Set 2020' },
        { code: 'WAR', name: 'War of the Spark' },
        { code: 'RNA', name: 'Ravnica Allegiance' },
        { code: 'GRN', name: 'Guilds of Ravnica' },
        { code: 'M19', name: 'Core Set 2019' },
        { code: 'DOM', name: 'Dominaria' },
        { code: 'RIX', name: 'Rivals of Ixalan' },
        { code: 'XLN', name: 'Ixalan' }
    ];
    
    const filteredSets = commonSets.filter(set => 
        set.name.toLowerCase().includes(query.toLowerCase()) ||
        set.code.toLowerCase().includes(query.toLowerCase())
    );
    
    if (filteredSets.length === 0) {
        resultsContainer.innerHTML = '<div class="no-results">No sets found. Try a different search term.</div>';
        return;
    }
    
    const resultsHtml = filteredSets.map(set => `
        <div class="set-search-result" onclick="selectSearchedSetReview('${set.code}', '${set.name}')">
            <div class="set-code">${set.code}</div>
            <div class="set-name">${set.name}</div>
        </div>
    `).join('');
    
    resultsContainer.innerHTML = resultsHtml;
}

async function selectSearchedSetReview(setCode, setName) {
    const cardId = window.currentSetSearchCardId;
    if (!cardId) return;
    
    try {
        await updateCardSetReview(cardId, setCode, setName);
        closeSetSearchModalReview();
    } catch (error) {
        console.error('Error selecting searched set:', error);
    }
}

async function applyManualSetReview() {
    const setCode = document.getElementById('manualSetCodeReview').value.trim();
    const setName = document.getElementById('manualSetNameReview').value.trim();
    const cardId = window.currentSetSearchCardId;
    
    if (!setCode || !setName || !cardId) {
        alert('Please enter both set code and set name');
        return;
    }
    
    try {
        await updateCardSetReview(cardId, setCode, setName);
        closeSetSearchModalReview();
    } catch (error) {
        console.error('Error applying manual set:', error);
    }
}

async function updateCardSetReview(cardId, setCode, setName) {
    const response = await fetch(`/cards/${cardId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            set_code: setCode,
            set_name: setName
        })
    });
    
    if (!response.ok) {
        throw new Error('Failed to update card set');
    }
    
    // Update the review interface
    const review = window.currentUnknownSetsReview;
    if (review) {
        review.cards.splice(review.currentIndex, 1);
        review.totalCards--;
        
        if (review.totalCards === 0) {
            displayUnknownSetsReview([]);
        } else if (review.currentIndex >= review.totalCards) {
            showUnknownSetCard(review.totalCards - 1);
        } else {
            showUnknownSetCard(review.currentIndex);
        }
    }
    
    console.log(`Updated card ${cardId} set to: ${setName} (${setCode})`);
}

// AI Service Logs functionality
function showAILogs() {
    const modal = document.getElementById('aiLogsModal');
    const body = document.getElementById('aiLogsBody');
    
    // Show loading state
    body.innerHTML = `
        <div class="ai-logs-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading AI service status...</p>
        </div>
    `;
    
    modal.style.display = 'flex';
    
    // Hide tools dropdown
    const dropdown = document.getElementById('toolsDropdown');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    
    // Load AI logs data
    loadAILogsData();
}

function closeAILogsModal() {
    const modal = document.getElementById('aiLogsModal');
    modal.style.display = 'none';
}

async function loadAILogsData() {
    try {
        // Fetch both health and error data
        const [healthResponse, errorsResponse] = await Promise.all([
            fetch('/debug/ai-health'),
            fetch('/debug/ai-errors')
        ]);
        
        const healthData = await healthResponse.json();
        const errorsData = await errorsResponse.json();
        
        displayAILogsData(healthData, errorsData);
        
    } catch (error) {
        console.error('Error loading AI logs:', error);
        displayAILogsError(error.message);
    }
}

function displayAILogsData(healthData, errorsData) {
    const body = document.getElementById('aiLogsBody');
    
    const healthSection = createHealthSection(healthData);
    const errorSection = createErrorSection(errorsData);
    
    body.innerHTML = `
        <div class="ai-logs-content">
            ${healthSection}
            ${errorSection}
            <div class="ai-logs-actions">
                <button class="ai-logs-btn" onclick="showFullAILogs()">
                    <i class="fas fa-file-alt"></i> Full Logs
                </button>
                <button class="ai-logs-btn refresh" onclick="refreshAILogs()">
                    <i class="fas fa-sync-alt"></i> Refresh
                </button>
                <button class="ai-logs-btn" onclick="closeAILogsModal()">
                    Close
                </button>
            </div>
        </div>
    `;
}

function createHealthSection(healthData) {
    const isHealthy = healthData.status === 'healthy';
    const healthIcon = isHealthy ? 'fas fa-check-circle' : 'fas fa-exclamation-triangle';
    const healthClass = isHealthy ? 'healthy' : 'error';
    
    return `
        <div class="ai-health-section">
            <div class="ai-health-title">
                <i class="${healthIcon}"></i>
                AI Service Health
            </div>
            <div class="ai-health-status">
                <div class="ai-health-item">
                    <span class="ai-health-label">Status</span>
                    <span class="ai-health-value ${healthClass}">
                        ${isHealthy ? 'Healthy' : healthData.last_error || 'Unhealthy'}
                    </span>
                </div>
                <div class="ai-health-item">
                    <span class="ai-health-label">API Key</span>
                    <span class="ai-health-value">${healthData.api_key_present ? 'Present' : 'Missing'}</span>
                </div>
                <div class="ai-health-item">
                    <span class="ai-health-label">Rate Limit</span>
                    <span class="ai-health-value">${healthData.rate_limit_interval || 0}s</span>
                </div>
                <div class="ai-health-item">
                    <span class="ai-health-label">Last Error</span>
                    <span class="ai-health-value">${healthData.last_error || 'None'}</span>
                </div>
            </div>
        </div>
    `;
}

function createErrorSection(errorsData) {
    const hasError = errorsData.has_errors && errorsData.last_error;
    const sectionClass = hasError ? '' : 'no-error';
    const errorIcon = hasError ? 'fas fa-exclamation-circle' : 'fas fa-check-circle';
    
    if (!hasError) {
        return `
            <div class="ai-error-section ${sectionClass}">
                <div class="ai-error-title">
                    <i class="${errorIcon}"></i>
                    Recent Errors
                </div>
                <div class="ai-no-error">
                    <i class="fas fa-thumbs-up"></i>
                    No recent errors detected
                </div>
            </div>
        `;
    }
    
    const error = errorsData.last_error;
    const errorTypeClass = getErrorTypeClass(error.error_type);
    
    return `
        <div class="ai-error-section ${sectionClass}">
            <div class="ai-error-title">
                <i class="${errorIcon}"></i>
                Recent Errors
            </div>
            <div class="ai-error-details">
                <div class="ai-error-item">
                    <span class="ai-error-label">Error Type:</span>
                    <span class="ai-error-type ${errorTypeClass}">${error.error_type}</span>
                </div>
                <div class="ai-error-item">
                    <span class="ai-error-label">Timestamp:</span>
                    <span class="ai-error-value">${new Date(error.timestamp).toLocaleString()}</span>
                </div>
                <div class="ai-error-item">
                    <span class="ai-error-label">Quota Issue:</span>
                    <span class="ai-error-value">${error.is_quota_error ? 'Yes' : 'No'}</span>
                </div>
                <div class="ai-error-item">
                    <span class="ai-error-label">Rate Limited:</span>
                    <span class="ai-error-value">${error.is_rate_limit ? 'Yes' : 'No'}</span>
                </div>
                <div class="ai-error-item">
                    <span class="ai-error-label">Message:</span>
                    <span class="ai-error-value">${error.message}</span>
                </div>
            </div>
        </div>
    `;
}

function getErrorTypeClass(errorType) {
    switch (errorType) {
        case 'QUOTA_EXCEEDED':
            return 'quota';
        case 'RATE_LIMIT':
            return 'rate-limit';
        case 'DEPRECATED_MODEL':
            return 'deprecated';
        default:
            return 'unknown';
    }
}

function refreshAILogs() {
    const body = document.getElementById('aiLogsBody');
    
    // Show loading state
    body.innerHTML = `
        <div class="ai-logs-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Refreshing AI service status...</p>
        </div>
    `;
    
    // Reload data
    loadAILogsData();
}

// Show full AI logs in a new modal
async function showFullAILogs() {
    try {
        const response = await fetch('/debug/ai-logs-full');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Create a new modal for full logs
        const fullLogsModal = document.createElement('div');
        fullLogsModal.className = 'modal';
        fullLogsModal.id = 'fullLogsModal';
        fullLogsModal.innerHTML = `
            <div class="modal-content full-logs-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-file-alt"></i> Complete AI Service Logs</h3>
                    <button class="close-btn" onclick="closeFullLogsModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="full-logs-content">
                        <pre id="fullLogsText">${data.logs || 'No logs available'}</pre>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(fullLogsModal);
        fullLogsModal.style.display = 'flex';
        
        // Add escape key handler
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                closeFullLogsModal();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
    } catch (error) {
        console.error('Error loading full logs:', error);
        alert('Failed to load full logs: ' + error.message);
    }
}

function closeFullLogsModal() {
    const modal = document.getElementById('fullLogsModal');
    if (modal) {
        modal.remove();
    }
}

function displayAILogsError(errorMessage) {
    const body = document.getElementById('aiLogsBody');
    
    body.innerHTML = `
        <div class="ai-logs-content">
            <div class="ai-error-section">
                <div class="ai-error-title">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error Loading AI Logs
                </div>
                <div class="ai-error-details">
                    <p>Failed to load AI service information:</p>
                    <pre style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px;">${errorMessage}</pre>
                </div>
            </div>
            <div class="ai-logs-actions">
                <button class="ai-logs-btn refresh" onclick="refreshAILogs()">
                    <i class="fas fa-sync-alt"></i> Retry
                </button>
                <button class="ai-logs-btn" onclick="closeAILogsModal()">
                    Close
                </button>
            </div>
        </div>
    `;
}

// Handle click outside AI logs modal to close
document.addEventListener('click', function(event) {
    const modal = document.getElementById('aiLogsModal');
    if (event.target === modal) {
        closeAILogsModal();
    }
});

// Rescan a card image from the unknown sets review
async function rescanCard(scanId) {
    try {
        // Get the scan information to find the image file
        const scanInfoResponse = await fetch(`/scan/${scanId}/info`);
        if (!scanInfoResponse.ok) {
            throw new Error('Failed to get scan information');
        }
        
        const scanInfo = await scanInfoResponse.json();
        
        // Get the image file from the server
        const imageResponse = await fetch(`/${scanInfo.image_filename}`);
        if (!imageResponse.ok) {
            throw new Error('Failed to get scan image');
        }
        
        const imageBlob = await imageResponse.blob();
        const imageFile = new File([imageBlob], scanInfo.image_filename, {
            type: imageBlob.type
        });
        
        // Close the unknown sets modal
        closeUnknownSetsModal();
        
        // Start the scan process with the image file
        const scanResult = await uploadAndScan([imageFile]);
        
        if (scanResult.success) {
            // Open scanning modal and start the workflow
            await showScanningModal(scanResult.scan_id, [imageFile]);
        } else {
            alert(`Error starting rescan: ${scanResult.error}`);
        }
        
    } catch (error) {
        console.error('Error rescanning card:', error);
        alert('Error rescanning card. Please try again.');
    }
}

// Show AI response modal
async function showAIResponse(scanId) {
    try {
        const response = await fetch(`/scan/${scanId}/ai-response`);
        if (!response.ok) {
            throw new Error('Failed to fetch AI response');
        }
        
        const data = await response.json();
        
        // Create AI response modal
        const modal = document.createElement('div');
        modal.className = 'modal ai-response-modal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content ai-response-content">
                <div class="modal-header">
                    <h3><i class="fas fa-brain"></i> AI Response Details - Scan #${scanId}</h3>
                    <button class="close-btn" onclick="closeAIResponseModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="ai-response-body">
                    <div class="ai-response-section">
                        ${createAIResponseContent(data)}
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.appendChild(modal);
        
        // Store reference for closing
        window.currentAIResponseModal = modal;
        
        // Add escape key handler
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                closeAIResponseModal();
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
    } catch (error) {
        console.error('Error fetching AI response:', error);
        alert('Failed to load AI response details. Please try again.');
    }
}

// Create AI response content
function createAIResponseContent(data) {
    if (!data.has_ai_response) {
        return `
            <div class="ai-response-section">
                <div class="ai-response-status no-response">
                    <i class="fas fa-info-circle"></i>
                    <h4>No AI Response Available</h4>
                    <p>${data.message || 'No raw AI response was stored for this scan.'}</p>
                </div>
            </div>
        `;
    }
    
    // Parse the response to detect if it's a refusal or successful identification
    const rawResponse = data.ai_raw_response || '';
    const isRefusal = rawResponse.toLowerCase().includes("i'm unable to identify") || 
                     rawResponse.toLowerCase().includes("i cannot identify") ||
                     rawResponse.toLowerCase().includes("i can't identify");
    
    const createdAt = data.created_at ? new Date(data.created_at).toLocaleString() : 'Unknown';
    
    return `
        <div class="ai-response-section">
            <div class="ai-response-meta">
                <div class="ai-response-info">
                    <span class="ai-response-label">Scan ID:</span>
                    <span class="ai-response-value">${data.scan_id}</span>
                </div>
                <div class="ai-response-info">
                    <span class="ai-response-label">Cards Found:</span>
                    <span class="ai-response-value">${data.cards_found}</span>
                </div>
                <div class="ai-response-info">
                    <span class="ai-response-label">Response Time:</span>
                    <span class="ai-response-value">${createdAt}</span>
                </div>
                <div class="ai-response-info">
                    <span class="ai-response-label">Response Type:</span>
                    <span class="ai-response-value ${isRefusal ? 'refusal' : 'success'}">
                        ${isRefusal ? 'AI Refusal' : 'Successful Identification'}
                    </span>
                </div>
            </div>
            
            <div class="ai-response-content-section">
                <h4><i class="fas fa-robot"></i> Raw AI Response</h4>
                <div class="ai-response-text ${isRefusal ? 'refusal-text' : 'success-text'}">
                    <pre>${rawResponse}</pre>
                </div>
            </div>
            
            ${isRefusal ? `
                <div class="ai-response-help">
                    <h4><i class="fas fa-lightbulb"></i> Tips for Better Results</h4>
                    <ul>
                        <li>Ensure good lighting and clear card visibility</li>
                        <li>Try capturing cards individually rather than in groups</li>
                        <li>Make sure card text and set symbols are clearly visible</li>
                        <li>Avoid reflections and shadows on card surfaces</li>
                        <li>Take photos from directly above the cards</li>
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
}

// Close AI response modal
function closeAIResponseModal() {
    if (window.currentAIResponseModal) {
        document.body.removeChild(window.currentAIResponseModal);
        window.currentAIResponseModal = null;
    }
}

// Camera functionality
function initializeCamera() {
    cameraModal = document.getElementById('cameraModal');
    cameraVideo = document.getElementById('cameraVideo');
    cameraCanvas = document.getElementById('cameraCanvas');
    
    // Camera modal event listeners
    const closeCameraBtn = document.getElementById('closeCameraBtn');
    const cancelCameraBtn = document.getElementById('cancelCameraBtn');
    const captureBtn = document.getElementById('captureBtn');
    
    if (closeCameraBtn) {
        closeCameraBtn.addEventListener('click', closeCameraModal);
    }
    if (cancelCameraBtn) {
        cancelCameraBtn.addEventListener('click', closeCameraModal);
    }
    if (captureBtn) {
        captureBtn.addEventListener('click', capturePhoto);
    }
    
    // Close modal when clicking outside
    if (cameraModal) {
        cameraModal.addEventListener('click', (e) => {
            if (e.target === cameraModal) {
                closeCameraModal();
            }
        });
    }
}

function handleCameraClick() {
    // Check if Camera API is supported
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Use modern Camera API
        openCameraModal();
    } else {
        // Fallback to file input with camera capture
        console.log('📷 DEBUG: Using file input fallback for camera');
        triggerCameraFileInput();
    }
}

function triggerCameraFileInput() {
    // Create a temporary file input for camera capture
    const cameraFileInput = document.createElement('input');
    cameraFileInput.type = 'file';
    cameraFileInput.accept = 'image/*';
    cameraFileInput.capture = 'environment';
    cameraFileInput.style.display = 'none';
    
    cameraFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            console.log('📷 DEBUG: Camera file selected via fallback');
            handleFileSelect(e);
        }
        // Clean up
        document.body.removeChild(cameraFileInput);
    });
    
    // Add to DOM temporarily and trigger
    document.body.appendChild(cameraFileInput);
    cameraFileInput.click();
}

async function openCameraModal() {
    try {
        console.log('📷 DEBUG: Opening camera modal');
        
        // Check if getUserMedia is supported
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera API not supported in this browser');
        }
        
        // Check permissions first
        try {
            const permission = await navigator.permissions.query({ name: 'camera' });
            console.log('📷 DEBUG: Camera permission status:', permission.state);
            
            if (permission.state === 'denied') {
                throw new Error('Camera permission denied. Please enable camera access in your browser settings.');
            }
        } catch (permError) {
            console.log('📷 DEBUG: Permission API not available, proceeding with camera request');
        }
        
        // Try with rear camera first
        let constraints = {
            video: {
                facingMode: 'environment',
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            }
        };
        
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        } catch (rearCameraError) {
            console.log('📷 DEBUG: Rear camera failed, trying any camera:', rearCameraError.message);
            
            // Fallback to any available camera
            constraints = {
                video: {
                    width: { ideal: 1920 },
                    height: { ideal: 1080 }
                }
            };
            
            cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        }
        
        cameraVideo.srcObject = cameraStream;
        cameraModal.style.display = 'block';
        
        console.log('📷 DEBUG: Camera stream started');
    } catch (error) {
        console.error('📷 ERROR: Failed to access camera:', error);
        
        let errorMessage = 'Unable to access camera. ';
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            errorMessage += 'Please allow camera access when prompted, or check your browser settings to enable camera permissions for this site.';
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            errorMessage += 'No camera found on this device.';
        } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
            errorMessage += 'Camera is already in use by another application.';
        } else if (error.name === 'OverconstrainedError' || error.name === 'ConstraintNotSatisfiedError') {
            errorMessage += 'Camera does not meet the required specifications.';
        } else if (error.name === 'NotSupportedError') {
            errorMessage += 'Camera API not supported in this browser.';
        } else {
            errorMessage += error.message || 'Unknown error occurred.';
        }
        
        alert(errorMessage);
    }
}

function closeCameraModal() {
    console.log('📷 DEBUG: Closing camera modal');
    
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    
    if (cameraModal) {
        cameraModal.style.display = 'none';
    }
    
    if (cameraVideo) {
        cameraVideo.srcObject = null;
    }
}

async function capturePhoto() {
    if (!cameraVideo || !cameraCanvas) {
        console.error('📷 ERROR: Camera elements not found');
        return;
    }
    
    try {
        console.log('📷 DEBUG: Capturing photo');
        
        // Set canvas size to match video
        cameraCanvas.width = cameraVideo.videoWidth;
        cameraCanvas.height = cameraVideo.videoHeight;
        
        // Draw video frame to canvas
        const ctx = cameraCanvas.getContext('2d');
        ctx.drawImage(cameraVideo, 0, 0);
        
        // Convert canvas to blob
        cameraCanvas.toBlob(async (blob) => {
            if (blob) {
                // Create a File object from the blob
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                const file = new File([blob], `camera-capture-${timestamp}.jpg`, { type: 'image/jpeg' });
                
                console.log('📷 DEBUG: Photo captured, processing...');
                
                // Close modal first
                closeCameraModal();
                
                // Process the captured image
                await processFiles([file]);
            }
        }, 'image/jpeg', 0.8);
        
    } catch (error) {
        console.error('📷 ERROR: Failed to capture photo:', error);
        alert('Failed to capture photo. Please try again.');
    }
}

// ... existing code ...

function exportCollection() {
    // Show the export modal instead of immediately exporting
    const exportModal = document.getElementById('exportModal');
    const exportFormat = document.getElementById('exportFormat');
    
    // Set default values - CSV format
    exportFormat.value = 'csv';
    
    exportModal.style.display = 'flex';
}

function closeExportModal() {
    const exportModal = document.getElementById('exportModal');
    const exportForm = document.querySelector('.export-form');
    const exportProgress = document.getElementById('exportProgress');
    
    exportModal.style.display = 'none';
    exportForm.style.display = 'block';
    exportProgress.style.display = 'none';
}



async function startExport() {
    const exportForm = document.querySelector('.export-form');
    const exportProgress = document.getElementById('exportProgress');
    const exportProgressFill = document.getElementById('exportProgressFill');
    const exportProgressText = document.getElementById('exportProgressText');
    
    const format = document.getElementById('exportFormat').value;
    
    // Show progress
    exportForm.style.display = 'none';
    exportProgress.style.display = 'block';
    
    try {
        // Update progress
        exportProgressFill.style.width = '20%';
        exportProgressText.textContent = 'Preparing export...';
        
        // Use new download endpoint
        const response = await fetch('/export/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                format: format
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Export failed');
        }
        
        exportProgressFill.style.width = '50%';
        exportProgressText.textContent = 'Downloading file...';
        
        // Get the filename from response headers
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `magic_cards_export.${format === 'excel' ? 'xlsx' : 'csv'}`;
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=([^;]+)/);
            if (match) {
                filename = match[1].replace(/"/g, '');
            }
        }
        
        // Convert response to blob and trigger download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
            exportProgressFill.style.width = '100%';
            exportProgressText.textContent = 'Export completed!';
            
            // Close modal after short delay
            setTimeout(() => {
                closeExportModal();
                
            // Show success message
                const notification = document.createElement('div');
                notification.className = 'notification success';
                notification.innerHTML = `
                    <i class="fas fa-check-circle"></i>
                <span>Export completed successfully!<br><small>File: ${filename} downloaded</small></span>
                `;
                document.body.appendChild(notification);
                
                // Remove notification after 5 seconds
                setTimeout(() => {
                    notification.remove();
                }, 5000);
            }, 1000);
        
    } catch (error) {
        console.error('Export error:', error);
        
        // Reset form
        exportForm.style.display = 'block';
        exportProgress.style.display = 'none';
        
        // Show error message
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.innerHTML = `
            <i class="fas fa-exclamation-circle"></i>
            <span>Export failed: ${error.message}</span>
        `;
        document.body.appendChild(notification);
        
        // Remove notification after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
}

// ... rest of the existing code ...

// Card-Scan Association Tool
let currentAssociationCard = null;
let availableScans = [];
let currentScanIndex = 0;

async function showCardScanAssociationTool() {
    // First, get a random card to start with, or prompt user to select
    await loadRandomCardForAssociation();
}

async function loadRandomCardForAssociation() {
    try {
        // Get all cards to choose from
        const response = await fetch('/cards?view_mode=individual');
        const data = await response.json();
        
        if (data.cards && data.cards.length > 0) {
            // Start with the first card
            const randomCard = data.cards[0];
            await loadCardForAssociation(randomCard.id);
        } else {
            alert('No cards found in database');
        }
    } catch (error) {
        console.error('Error loading random card:', error);
        alert('Error loading card data');
    }
}

async function loadCardForAssociation(cardId) {
    try {
        // Show the modal
        document.getElementById('cardScanAssociationModal').style.display = 'flex';
        
        // Load card data and available scans in parallel
        const [cardResponse, scansResponse] = await Promise.all([
            fetch(`/api/card-scan-tool/card/${cardId}`),
            fetch('/api/card-scan-tool/scans')
        ]);
        
        const cardData = await cardResponse.json();
        const scansData = await scansResponse.json();
        
        currentAssociationCard = cardData;
        availableScans = scansData.scans;
        
        // Find current scan index
        currentScanIndex = 0;
        if (cardData.current_scan) {
            const scanIndex = availableScans.findIndex(scan => scan.id === cardData.current_scan.id);
            if (scanIndex !== -1) {
                currentScanIndex = scanIndex;
            }
        }
        
        // Display the interface
        displayCardScanAssociationInterface();
        
    } catch (error) {
        console.error('Error loading card for association:', error);
        alert('Error loading card data');
    }
}

function displayCardScanAssociationInterface() {
    const content = document.getElementById('cardScanAssociationContent');
    const card = currentAssociationCard.card;
    const currentScan = availableScans[currentScanIndex];
    
    content.innerHTML = `
        <div class="card-scan-association-interface">
            <!-- Card Selection Header -->
            <div class="association-header">
                <h4>Fixing Scan Association for Card</h4>
                <div class="card-selector">
                    <button class="btn btn-secondary" onclick="selectDifferentCard()">
                        <i class="fas fa-exchange-alt"></i> Select Different Card
                    </button>
                </div>
            </div>
            
            <!-- Main Interface -->
            <div class="association-main">
                <!-- Left Side: Card Info -->
                <div class="association-card-side">
                    <h5><i class="fas fa-magic"></i> Card Information</h5>
                    <div class="card-info-display">
                        <div class="card-image-container">
                            ${card.image_url ? 
                                `<img src="${card.image_url}" alt="${card.name}" class="association-card-image">` :
                                `<div class="no-image-placeholder">No Image</div>`
                            }
                        </div>
                        <div class="card-details">
                            <h6>${card.name}</h6>
                            <p><strong>Set:</strong> ${card.set_name} (${card.set_code})</p>
                            <p><strong>Collector #:</strong> ${card.collector_number || 'N/A'}</p>
                            <p><strong>Condition:</strong> ${card.condition}</p>
                            <p><strong>Count:</strong> ${card.count}</p>
                            <p><strong>Current Scan ID:</strong> ${card.scan_id || 'None'}</p>
                            <p><strong>First Seen:</strong> ${formatDateTime(card.first_seen)}</p>
                        </div>
                    </div>
                </div>
                
                <!-- Right Side: Scan Selection -->
                <div class="association-scan-side">
                    <h5><i class="fas fa-camera"></i> Scan Selection</h5>
                    <div class="scan-navigation">
                        <button class="btn btn-secondary" onclick="previousScan()" ${currentScanIndex === 0 ? 'disabled' : ''}>
                            <i class="fas fa-chevron-left"></i> Previous
                        </button>
                        <span class="scan-counter">${currentScanIndex + 1} of ${availableScans.length}</span>
                        <button class="btn btn-secondary" onclick="nextScan()" ${currentScanIndex >= availableScans.length - 1 ? 'disabled' : ''}>
                            <i class="fas fa-chevron-right"></i> Next
                        </button>
                    </div>
                    
                    <div class="current-scan-display">
                        <h6>Scan #${currentScan.id}</h6>
                        <p><strong>Date:</strong> ${formatDateTime(currentScan.created_at)}</p>
                        <p><strong>Cards Found:</strong> ${currentScan.total_cards_found}</p>
                        <p><strong>Images:</strong> ${currentScan.images.length}</p>
                        
                        <!-- Scan Images -->
                        <div class="scan-images-grid">
                            ${currentScan.images.map(img => `
                                <div class="scan-image-item" onclick="selectScanImage(${img.id})" data-image-id="${img.id}">
                                    <img src="/uploads/${img.filename}" alt="Scan Image" class="scan-thumbnail">
                                    <div class="scan-image-info">
                                        <small>${img.cards_found} cards</small>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Action Buttons -->
            <div class="association-actions">
                <button class="btn btn-primary" onclick="associateCardWithCurrentScan()">
                    <i class="fas fa-link"></i> Associate with Scan #${currentScan.id}
                </button>
                <button class="btn btn-secondary" onclick="associateCardWithSelectedImage()">
                    <i class="fas fa-image"></i> Associate with Selected Image
                </button>
                <div class="association-status" id="associationStatus"></div>
            </div>
        </div>
    `;
    
    // Highlight current scan if it matches the card's scan
    if (currentAssociationCard.current_scan && currentAssociationCard.current_scan.id === currentScan.id) {
        const status = document.getElementById('associationStatus');
        status.innerHTML = '<i class="fas fa-check-circle"></i> This is the current scan association';
        status.className = 'association-status current-association';
    }
}

function previousScan() {
    if (currentScanIndex > 0) {
        currentScanIndex--;
        displayCardScanAssociationInterface();
    }
}

function nextScan() {
    if (currentScanIndex < availableScans.length - 1) {
        currentScanIndex++;
        displayCardScanAssociationInterface();
    }
}

let selectedScanImageId = null;

function selectScanImage(imageId) {
    // Remove previous selection
    document.querySelectorAll('.scan-image-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked image
    const imageItem = document.querySelector(`[data-image-id="${imageId}"]`);
    if (imageItem) {
        imageItem.classList.add('selected');
        selectedScanImageId = imageId;
    }
}

async function associateCardWithCurrentScan() {
    const currentScan = availableScans[currentScanIndex];
    await updateCardScanAssociation(currentScan.id, null);
}

async function associateCardWithSelectedImage() {
    if (!selectedScanImageId) {
        alert('Please select a scan image first');
        return;
    }
    
    const currentScan = availableScans[currentScanIndex];
    await updateCardScanAssociation(currentScan.id, selectedScanImageId);
}

async function updateCardScanAssociation(scanId, scanImageId) {
    try {
        const statusDiv = document.getElementById('associationStatus');
        statusDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating association...';
        statusDiv.className = 'association-status updating';
        
        const response = await fetch(`/api/card-scan-tool/card/${currentAssociationCard.card.id}/associate`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                scan_id: scanId,
                scan_image_id: scanImageId
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusDiv.innerHTML = '<i class="fas fa-check-circle"></i> Association updated successfully!';
            statusDiv.className = 'association-status success';
            
            // Reload the card data to show updated association
            setTimeout(() => {
                loadCardForAssociation(currentAssociationCard.card.id);
            }, 1000);
            
        } else {
            throw new Error(result.message || 'Association failed');
        }
        
    } catch (error) {
        console.error('Error updating association:', error);
        const statusDiv = document.getElementById('associationStatus');
        statusDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error updating association';
        statusDiv.className = 'association-status error';
    }
}

async function selectDifferentCard() {
    // For now, just load a random card. Could be enhanced with a card picker
    await loadRandomCardForAssociation();
}

function closeCardScanAssociationTool() {
    document.getElementById('cardScanAssociationModal').style.display = 'none';
    currentAssociationCard = null;
    availableScans = [];
    currentScanIndex = 0;
    selectedScanImageId = null;
}

// Updated function to view the specific scan image that produced this card
async function viewCardScanImage(cardId, cardName) {
    try {
        // Get the specific scan image that produced this card
        const response = await fetch(`/card/${cardId}/scan-image`);
        if (!response.ok) {
            throw new Error('Failed to fetch card scan image');
        }
        
        const scanImageData = await response.json();
        
        if (!scanImageData.success || !scanImageData.has_scan_image) {
            alert(scanImageData.message || 'No scan image found for this card');
            return;
        }
        
        // Show the specific scan image that produced this card
        showFullScanImage(
            scanImageData.filename, 
            scanImageData.image_url, 
            `Original scan image for: ${cardName}`
        );
        
    } catch (error) {
        console.error('Error viewing card scan image:', error);
        alert('Failed to load scan image');
    }
}

// Keep the old function for backward compatibility (scan history, etc.)
async function viewScanImage(scanId, cardName) {
    try {
        // Fetch scan data to get the image filename
        const response = await fetch(`/scan/${scanId}/details`);
        if (!response.ok) {
            throw new Error('Failed to fetch scan details');
        }
        
        const scanData = await response.json();
        if (!scanData.success || !scanData.scan.images || scanData.scan.images.length === 0) {
            alert('No scan image found for this card');
            return;
        }
        
        // Use the first image from the scan
        const imageFilename = scanData.scan.images[0].filename;
        const imageUrl = `/uploads/${imageFilename}`;
        
        // Show the scan image in full screen
        showFullScanImage(imageFilename, imageUrl, `Original scan for: ${cardName}`);
        
    } catch (error) {
        console.error('Error viewing scan image:', error);
        alert('Failed to load scan image');
    }
}

// AI Preference functionality
async function showAIPreference() {
    // Close tools dropdown
    const dropdown = document.getElementById('toolsDropdown');
    dropdown.classList.remove('show');
    
    // Show modal
    const modal = document.getElementById('aiPreferenceModal');
    modal.style.display = 'flex';
    
    // Load AI preference data
    await loadAIPreference();
}

function closeAIPreferenceModal() {
    const modal = document.getElementById('aiPreferenceModal');
    modal.style.display = 'none';
}

async function loadAIPreference() {
    const body = document.getElementById('aiPreferenceBody');
    
    // Show loading state
    body.innerHTML = `
        <div class="ai-preference-loading">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading AI preference settings...</p>
        </div>
    `;
    
    try {
        const response = await fetch('/api/ai-preference');
        if (!response.ok) {
            throw new Error('Failed to load AI preference');
        }
        
        const preferenceData = await response.json();
        if (preferenceData.success) {
            displayAIPreference(preferenceData);
        } else {
            throw new Error(preferenceData.error || 'Failed to load preference');
        }
        
    } catch (error) {
        console.error('Error loading AI preference:', error);
        body.innerHTML = `
            <div class="ai-preference-error">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error Loading Settings</h3>
                <p>Failed to load AI preference settings. Please try again.</p>
                <button class="btn btn-primary" onclick="loadAIPreference()">
                    <i class="fas fa-refresh"></i> Retry
                </button>
            </div>
        `;
    }
}

function displayAIPreference(preferenceData) {
    const body = document.getElementById('aiPreferenceBody');
    
    const primary = preferenceData.primary;
    
    body.innerHTML = `
        <div class="ai-preference-content">
            <div class="preference-info">
                <p><i class="fas fa-info-circle"></i> Choose which AI model to use as the primary processor for card identification.</p>
            </div>
            
            <div class="preference-options">
                <div class="preference-option ${primary === 'claude' ? 'selected' : ''}" onclick="setAIPreference('claude')">
                    <div class="option-header">
                        <i class="fas fa-robot"></i>
                        <h4>Claude Vision</h4>
                        ${primary === 'claude' ? '<span class="primary-badge">Selected</span>' : ''}
                    </div>
                    <div class="option-details">
                        <p><strong>Model:</strong> Claude 3.5 Sonnet</p>
                        <p><strong>Strengths:</strong> High accuracy, detailed analysis</p>
                        <p><strong>Confidence:</strong> Percentage-based (e.g., "95%")</p>
                    </div>
                </div>
                
                <div class="preference-option ${primary === 'openai' ? 'selected' : ''}" onclick="setAIPreference('openai')">
                    <div class="option-header">
                        <i class="fas fa-brain"></i>
                        <h4>OpenAI GPT-4 Vision</h4>
                        ${primary === 'openai' ? '<span class="primary-badge">Selected</span>' : ''}
                    </div>
                    <div class="option-details">
                        <p><strong>Model:</strong> GPT-4o</p>
                        <p><strong>Strengths:</strong> Fast processing, broad knowledge</p>
                        <p><strong>Confidence:</strong> Level-based (High/Medium/Low)</p>
                    </div>
                </div>
            </div>
            
            <div class="preference-actions">
                <button class="btn btn-secondary" onclick="closeAIPreferenceModal()">
                    <i class="fas fa-times"></i> Close
                </button>
            </div>
        </div>
    `;
}

async function setAIPreference(model) {
    try {
        const response = await fetch('/api/ai-preference', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ primary: model })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update AI preference');
        }
        
        const result = await response.json();
        if (result.success) {
            // Show success message
            showNotification(`AI preference updated to ${model}`, 'success');
            
            // Reload the preference display
            await loadAIPreference();
        } else {
            throw new Error(result.error || 'Failed to update preference');
        }
        
    } catch (error) {
        console.error('Error setting AI preference:', error);
        showNotification(`Failed to update AI preference: ${error.message}`, 'error');
    }
}

// ... existing code ...

// Simple notification system
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}