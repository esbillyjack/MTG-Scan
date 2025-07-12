// Global variables
let cards = [];
let searchTerm = '';

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
    setupEventListeners();
    loadCards();
    loadStats();
});

// Setup event listeners
function setupEventListeners() {
    // File upload handling
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Search functionality
    searchInput.addEventListener('input', handleSearch);
    
    // Modal close handling
    cardModal.addEventListener('click', (e) => {
        if (e.target === cardModal) {
            closeModal();
        }
    });
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
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
    const files = e.dataTransfer.files;
    processFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    processFiles(files);
}

// Process uploaded files
async function processFiles(files) {
    if (files.length === 0) return;
    
    showLoading(true);
    showUploadProgress();
    
    try {
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            if (!file.type.startsWith('image/')) {
                alert('Please upload only image files.');
                continue;
            }
            
            // Update progress
            const progress = ((i + 1) / files.length) * 100;
            updateProgress(progress, `Processing ${file.name}...`);
            
            // Upload and process the file
            const result = await uploadAndProcess(file);
            
            if (result.success) {
                displayResults(result.results);
            } else {
                alert(`Error processing ${file.name}: ${result.error}`);
            }
        }
        
        // Refresh the database view
        await loadCards();
        await loadStats();
        
    } catch (error) {
        console.error('Error processing files:', error);
        alert('Error processing files. Please try again.');
    } finally {
        showLoading(false);
        hideUploadProgress();
    }
}

// Upload and process a single file
async function uploadAndProcess(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.text();
            throw new Error(error);
        }
        
        return await response.json();
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

// Load cards from database
async function loadCards() {
    try {
        const response = await fetch('/cards');
        const data = await response.json();
        
        cards = data.cards;
        displayCards();
    } catch (error) {
        console.error('Error loading cards:', error);
    }
}

// Display cards in the grid
function displayCards() {
    const filteredCards = filterCards();
    cardsGrid.innerHTML = '';
    
    filteredCards.forEach(card => {
        const cardElement = createDatabaseCard(card);
        cardsGrid.appendChild(cardElement);
    });
}

// Create a database card element
function createDatabaseCard(card) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'card-item';
    cardDiv.onclick = () => showCardDetails(card.id);
    
    cardDiv.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
        </div>
        <div class="card-info">
            <div class="card-name">${card.name}</div>
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
            <div class="card-count">Count: ${card.count}</div>
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
        
        document.getElementById('totalCards').textContent = stats.total_unique_cards;
        document.getElementById('totalCount').textContent = stats.total_card_count;
        document.getElementById('totalValue').textContent = `$${stats.total_value_usd.toFixed(2)}`;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Show card details modal
async function showCardDetails(cardId) {
    try {
        const response = await fetch(`/cards/${cardId}`);
        const card = await response.json();
        
        modalTitle.textContent = card.name;
        modalBody.innerHTML = createCardDetailHTML(card);
        
        cardModal.style.display = 'block';
    } catch (error) {
        console.error('Error loading card details:', error);
        alert('Error loading card details.');
    }
}

// Create card detail HTML
function createCardDetailHTML(card) {
    return `
        <div class="card-detail">
            <div class="detail-row">
                <strong>Name:</strong> ${card.name}
            </div>
            <div class="detail-row">
                <strong>Set:</strong> ${card.set_name || 'Unknown'}
            </div>
            <div class="detail-row">
                <strong>Rarity:</strong> ${card.rarity || 'Unknown'}
            </div>
            <div class="detail-row">
                <strong>Type:</strong> ${card.type_line || 'Unknown'}
            </div>
            <div class="detail-row">
                <strong>Mana Cost:</strong> ${card.mana_cost || 'None'}
            </div>
            <div class="detail-row">
                <strong>Count:</strong> ${card.count}
            </div>
            <div class="detail-row">
                <strong>Prices:</strong>
                <div class="price-details">
                    <span class="price price-usd">USD: $${(card.price_usd || 0).toFixed(2)}</span>
                    <span class="price price-eur">EUR: €${(card.price_eur || 0).toFixed(2)}</span>
                    <span class="price price-tix">TIX: ${(card.price_tix || 0).toFixed(2)}</span>
                </div>
            </div>
            ${card.oracle_text ? `
            <div class="detail-row">
                <strong>Oracle Text:</strong>
                <div class="oracle-text">${card.oracle_text}</div>
            </div>
            ` : ''}
            <div class="detail-row">
                <strong>First Seen:</strong> ${new Date(card.first_seen).toLocaleDateString()}
            </div>
            <div class="detail-row">
                <strong>Last Seen:</strong> ${new Date(card.last_seen).toLocaleDateString()}
            </div>
        </div>
    `;
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
    updateProgress(0, 'Starting upload...');
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
`;
document.head.appendChild(style); 