// Global variables
let cards = [];
let searchTerm = '';
let currentCardIndex = 0;
let viewMode = 'individual'; // 'individual' or 'stacked'

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
    addTestData(); // Add test data with real Magic cards
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
            const fanOverlay = document.getElementById('fanOverlay');
            if (fanOverlay && fanOverlay.style.display === 'block') {
                closeFanOverlay();
            } else {
                closeModal();
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
        // Display stacked cards
        filteredCards.forEach((card, index) => {
            const cardElement = createStackedCard(card, index);
            cardsGrid.appendChild(cardElement);
        });
    } else {
        // Display individual cards
        filteredCards.forEach((card, index) => {
            const cardElement = createDatabaseCard(card, index);
            cardsGrid.appendChild(cardElement);
        });
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
function createDatabaseCard(card, index) {
    const cardDiv = document.createElement('div');
    cardDiv.className = `card-item color-border-${getColorBorder(card.colors)}`;
    cardDiv.onclick = () => showCardDetails(index);
    
    // Add example indicator
    const exampleBadge = card.is_example ? '<span class="example-badge">EXAMPLE</span>' : '';
    
    cardDiv.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
            ${exampleBadge}
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
            ${card.condition ? `<div class="card-condition">Condition: ${card.condition}</div>` : ''}
        </div>
    `;
    
    return cardDiv;
}

// Create a stacked card element
function createStackedCard(card, index) {
    const cardDiv = document.createElement('div');
    cardDiv.className = `card-item stacked-card color-border-${getColorBorder(card.colors)}`;
    cardDiv.onclick = () => showStackedCardDetails(index);
    
    // Create stack count badge if there are multiple cards
    const stackBadge = card.total_cards > 1 ? 
        `<div class="stack-count-badge">${card.stack_count}</div>` : '';
    
    // Create example badge if it's an example card
    const exampleBadge = card.is_example ? 
        '<div class="example-badge">EXAMPLE</div>' : '';
    
    cardDiv.innerHTML = `
        <div class="card-image">
            ${card.image_url ? `<img src="${card.image_url}" alt="${card.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
            ${stackBadge}
            ${exampleBadge}
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
            <div class="card-count">${card.total_cards > 1 ? `Stack (${card.total_cards})` : `Count: ${card.stack_count}`}</div>
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
        
        // Update stats based on current view mode
        if (viewMode === 'stacked') {
            // For stacked view, show stack-related stats
            document.getElementById('totalCards').textContent = stats.owned_unique_cards || stats.total_unique_cards;
            document.getElementById('totalCount').textContent = stats.owned_card_count || stats.total_card_count;
        } else {
            // For individual view, show individual card stats
            document.getElementById('totalCards').textContent = stats.owned_unique_cards || stats.total_unique_cards;
            document.getElementById('totalCount').textContent = stats.owned_card_count || stats.total_card_count;
        }
        
        document.getElementById('totalValue').textContent = `$${(stats.owned_value_usd || stats.total_value_usd).toFixed(2)}`;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Show card details modal with navigation
function showCardDetails(cardIndex) {
    currentCardIndex = cardIndex;
    const filteredCards = filterCards();
    const card = filteredCards[cardIndex];
    
    if (!card) return;
    
    modalTitle.textContent = card.name;
    modalBody.innerHTML = createEnhancedCardDetailHTML(card, cardIndex, filteredCards.length);
    
    cardModal.style.display = 'block';
}

// Show stacked card details in fan-out overlay
function showStackedCardDetails(index) {
    const card = cards[index];
    if (!card) return;
    
    currentCardIndex = index;
    
    // Set the fan title
    document.getElementById('fanTitle').textContent = `${card.name} - Stack (${card.total_cards} cards)`;
    
    // Create fanned cards
    const fanContainer = document.getElementById('fanContainer');
    fanContainer.innerHTML = '';
    fanContainer.setAttribute('data-count', card.duplicates ? card.duplicates.length : 1);
    
    if (card.duplicates && card.duplicates.length > 0) {
        card.duplicates.forEach((duplicate, idx) => {
            const fanCard = createFanCard(duplicate, card, idx);
            fanContainer.appendChild(fanCard);
        });
    } else {
        // Single card in stack
        const fanCard = createFanCard(card, card, 0);
        fanContainer.appendChild(fanCard);
    }
    
    // Show fan overlay
    document.getElementById('fanOverlay').style.display = 'block';
}

// Create a fanned card element
function createFanCard(cardData, parentCard, index) {
    const fanCard = document.createElement('div');
    fanCard.className = `fan-card color-border-${getColorBorder(parentCard.colors)}`;
    
    // Add example indicator
    const exampleBadge = cardData.is_example ? '<span class="example-badge">EXAMPLE</span>' : '';
    
    fanCard.innerHTML = `
        <div class="card-image">
            ${parentCard.image_url ? `<img src="${parentCard.image_url}" alt="${parentCard.name}" style="width: 100%; height: 100%; object-fit: cover;">` : '<i class="fas fa-image"></i>'}
            ${exampleBadge}
        </div>
        <div class="card-info">
            <div class="card-name">${parentCard.name}</div>
            <div class="card-condition">Condition: ${cardData.condition || 'Unknown'}</div>
        </div>
    `;
    
    // Add click handler to show individual card details
    fanCard.onclick = (e) => {
        e.stopPropagation();
        showIndividualCardFromFan(cardData, parentCard);
    };
    
    return fanCard;
}

// Show individual card details from fan (closes fan and opens card modal)
function showIndividualCardFromFan(cardData, parentCard) {
    // Close fan overlay
    closeFanOverlay();
    
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

// Close fan overlay
function closeFanOverlay() {
    document.getElementById('fanOverlay').style.display = 'none';
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
    { value: 'special', label: 'Special' }
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
    { value: 'fdn', label: 'Foundations', code: 'FDN' }
];

// Create enhanced card detail HTML with navigation
function createEnhancedCardDetailHTML(card, index, total) {
    const condition = card.condition && CONDITION_OPTIONS.find(opt => opt.value === card.condition) ? card.condition : 'UNKNOWN';
    const conditionDropdown = `
        <select id="conditionDropdown" onchange="updateCardCondition(${card.id}, this.value)">
            ${CONDITION_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === condition ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    `;
    
    const rarity = card.rarity && RARITY_OPTIONS.find(opt => opt.value === card.rarity.toLowerCase()) ? card.rarity.toLowerCase() : 'unknown';
    const rarityDropdown = `
        <select id="rarityDropdown" onchange="updateCardRarity(${card.id}, this.value)">
            ${RARITY_OPTIONS.map(opt => `<option value="${opt.value}"${opt.value === rarity ? ' selected' : ''}>${opt.label}</option>`).join('')}
        </select>
    `;
    
    const setCode = card.set_code ? card.set_code.toLowerCase() : 'unknown';
    const setDropdown = `
        <select id="setDropdown" onchange="updateCardSet(${card.id}, this.value)">
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
                    <span class="detail-label">Set Code:</span>
                    <span class="detail-value" id="setCodeDisplay">${card.set_code || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Collector Number:</span>
                    <span class="detail-value">${card.collector_number || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Rarity:</span>
                    <span class="detail-value">${rarityDropdown}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Type:</span>
                    <span class="detail-value">${card.type_line || 'Unknown'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Mana Cost:</span>
                    <span class="detail-value">${card.mana_cost || 'None'}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Count:</span>
                    <span class="detail-value">${card.count}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Condition:</span>
                    <span class="detail-value">${conditionDropdown}</span>
                </div>
                ${card.notes ? `
                <div class="detail-row">
                    <span class="detail-label">Notes:</span>
                    <span class="detail-value notes-text">${card.notes}</span>
                </div>
                ` : ''}
                <div class="detail-row">
                    <span class="detail-label">Prices:</span>
                    <div class="price-details">
                        <span class="price-item price-usd">
                            <i class="fas fa-dollar-sign"></i>
                            $${(card.price_usd || 0).toFixed(2)}
                        </span>
                        <span class="price-item price-eur">
                            <i class="fas fa-euro-sign"></i>
                            €${(card.price_eur || 0).toFixed(2)}
                        </span>
                        <span class="price-item price-tix">
                            <i class="fas fa-coins"></i>
                            ${(card.price_tix || 0).toFixed(2)} TIX
                        </span>
                    </div>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Oracle Text:</span>
                    <div class="oracle-text">${card.oracle_text}</div>
                </div>
                <div class="detail-row">
                    <span class="detail-label">First Seen:</span>
                    <span class="detail-value">${new Date(card.first_seen).toLocaleDateString()}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Last Seen:</span>
                    <span class="detail-value">${new Date(card.last_seen).toLocaleDateString()}</span>
                </div>
                <div class="card-actions">
                    <button class="action-btn" onclick="editCard(${card.id})">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="action-btn delete-btn" onclick="deleteCard(${card.id})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
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
        alert('Error updating card condition.');
    }
}

// Update card rarity via API
async function updateCardRarity(cardId, newRarity) {
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
        alert('Error updating card rarity.');
    }
}

// Update card set and automatically update set code
async function updateCardSet(cardId, newSetValue) {
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
        alert('Error updating card set.');
    }
}

// Edit card details
async function editCard(cardId) {
    // This would open an edit modal - for now, just show an alert
    alert('Edit functionality coming soon!');
}

// Delete card
async function deleteCard(cardId) {
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
            alert('Error deleting card');
        }
    } catch (error) {
        console.error('Error deleting card:', error);
        alert('Error deleting card');
    }
}

// Navigate between cards
function navigateCard(direction) {
    const filteredCards = filterCards();
    const newIndex = currentCardIndex + direction;
    
    if (newIndex >= 0 && newIndex < filteredCards.length) {
        showCardDetails(newIndex);
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