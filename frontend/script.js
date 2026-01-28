// ===== CONFIGURATION =====
const API_BASE_URL = 'http://localhost:8000';

// ===== STATE MANAGEMENT =====
let currentUser = null;
let currentFilters = {
    country: '',
    category: '',
    sortBy: 'publishedAt',
    mode: 'trending' // trending, interest, userCountry
};
let availableCountries = [];
let newsCache = [];
let currentPage = 1;
let totalNewsLoaded = 0;
let isLoadingMore = false;
let hasMoreNews = true;
let nextPageToken = null;  // Store pagination token from NewsData.io
const ARTICLES_PER_PAGE = 10;

// ===== GLOBAL ARTICLE DEDUPLICATION =====
// Track all article URLs that have been displayed to prevent duplicates across pagination, 
// filter changes, and interest-based fetches
const loadedArticleUrls = new Set();
const loadedArticleTitles = new Map(); // Map of {title_timestamp -> url} for fallback deduplication

// ===== DOM ELEMENTS =====
const elements = {
    navBeforeLogin: document.getElementById('navBeforeLogin'),
    navAfterLogin: document.getElementById('navAfterLogin'),
    userName: document.getElementById('userName'),
    userButton: document.getElementById('userButton'),
    dropdownMenu: document.getElementById('dropdownMenu'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    mainContent: document.getElementById('mainContent'),
    loginModal: document.getElementById('loginModal'),
    signupModal: document.getElementById('signupModal'),
    newsGrid: document.getElementById('newsGrid'),
    loadingSpinner: document.getElementById('loadingSpinner'),
    errorMessage: document.getElementById('errorMessage'),
    noResults: document.getElementById('noResults'),
    themeToggle: document.getElementById('themeToggle'),
    themeToggleBeforeLogin: document.getElementById('themeToggleBeforeLogin'),
    countryFilter: document.getElementById('countryFilter'),
    categoryFilter: document.getElementById('categoryFilter'),
    sectionTitle: document.getElementById('sectionTitle'),
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toastMessage')
};

// ===== INITIALIZATION =====
function init() {
    checkAuth();
    initTheme();
    initEventListeners();
    loadCountries();
}

// ===== ARTICLE DEDUPLICATION HELPERS =====
/**
 * Check if an article is unique and hasn't been displayed before
 * Uses URL as primary key, title+publishedAt as fallback
 * 
 * @param {Object} article - Article object to check
 * @returns {boolean} - True if article is unique (not seen before)
 */
function isArticleUnique(article) {
    if (!article) return false;
    
    // Primary check: URL
    const articleUrl = article.url || article.link;
    if (articleUrl && loadedArticleUrls.has(articleUrl)) {
        return false;
    }
    
    // Fallback check: title + publishedAt (for articles without URL)
    const publishDate = article.publishedAt || article.pubDate;
    if (article.title && publishDate) {
        const titleDateKey = `${article.title.substring(0, 100)}_${publishDate}`;
        if (loadedArticleTitles.has(titleDateKey)) {
            return false;
        }
    }
    
    return true;
}

/**
 * Mark an article as loaded to prevent future duplicates
 * 
 * @param {Object} article - Article object to mark
 */
function markArticleAsLoaded(article) {
    if (!article) return;
    
    // Add URL to tracking set
    const articleUrl = article.url || article.link;
    if (articleUrl) {
        loadedArticleUrls.add(articleUrl);
    }
    
    // Add to fallback tracking map
    const publishDate = article.publishedAt || article.pubDate;
    if (article.title && publishDate) {
        const titleDateKey = `${article.title.substring(0, 100)}_${publishDate}`;
        loadedArticleTitles.set(titleDateKey, articleUrl || article.title);
    }
}

/**
 * Reset article tracking for a new session
 * Called when user clears filters or changes mode
 */
function resetArticleTracking() {
    loadedArticleUrls.clear();
    loadedArticleTitles.clear();
    console.log('🔄 Article tracking reset - new session started');
}

function initEventListeners() {
    // User dropdown toggle
    if (elements.userButton) {
        elements.userButton.addEventListener('click', (e) => {
            e.stopPropagation();
            const isExpanded = elements.dropdownMenu.classList.toggle('hidden');
            elements.userButton.setAttribute('aria-expanded', !isExpanded);
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!elements.userButton?.contains(e.target)) {
            elements.dropdownMenu?.classList.add('hidden');
            elements.userButton?.setAttribute('aria-expanded', 'false');
        }
    });
    
    // Country filter
    elements.countryFilter?.addEventListener('change', (e) => {
        currentFilters.country = e.target.value;
        currentFilters.mode = 'custom';
        setActiveFilterButton(''); // Deactivate quick filter buttons
        
        // Update styling
        if (e.target.value) {
            e.target.classList.add('active');
        } else {
            e.target.classList.remove('active');
        }
        
        // Update section title to show selected country
        if (e.target.value) {
            const selectedCountry = availableCountries.find(c => c.code === e.target.value);
            if (selectedCountry) {
                elements.sectionTitle.textContent = `News from ${selectedCountry.name} ${selectedCountry.flag}`;
            }
        } else {
            elements.sectionTitle.textContent = 'Trending News';
        }
        
        fetchMLEnhancedNews();
    });
    
    // Category filter
    elements.categoryFilter?.addEventListener('change', (e) => {
        currentFilters.category = e.target.value;
        
        // Update styling
        if (e.target.value) {
            e.target.classList.add('active');
        } else {
            e.target.classList.remove('active');
        }
        
        // Update section title to reflect category or country+category
        updateSectionTitle();
        
        fetchMLEnhancedNews();
    });
    
    // Theme toggles
    elements.themeToggle?.addEventListener('click', toggleTheme);
    elements.themeToggleBeforeLogin?.addEventListener('click', toggleTheme);
    
    // Close modals on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideModals();
        }
    });
}

// ===== LOAD COUNTRIES FROM API =====
async function loadCountries() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/countries`);
        const data = await response.json();
        
        if (data.status === 'success') {
            availableCountries = data.countries;
            populateCountryDropdown();
            console.log(`✅ Loaded ${availableCountries.length} countries`);
        }
    } catch (error) {
        console.error('Failed to load countries:', error);
        populateCountryDropdown(); // Use fallback
    }
}

function populateCountryDropdown() {
    if (!elements.countryFilter) return;
    
    elements.countryFilter.innerHTML = '';
    
    // Sort countries alphabetically by name (excluding Global)
    let countries = availableCountries.length > 0 ? availableCountries : [
        { code: '', name: 'Global', flag: '🌍' },
        { code: 'us', name: 'United States', flag: '🇺🇸' },
        { code: 'gb', name: 'United Kingdom', flag: '🇬🇧' },
        { code: 'in', name: 'India', flag: '🇮🇳' },
        { code: 'au', name: 'Australia', flag: '🇦🇺' },
        { code: 'ca', name: 'Canada', flag: '🇨🇦' }
    ];
    
    // Sort by name except Global which goes first
    const globalCountry = countries.find(c => c.code === '');
    const otherCountries = countries.filter(c => c.code !== '').sort((a, b) => a.name.localeCompare(b.name));
    const sortedCountries = globalCountry ? [globalCountry, ...otherCountries] : otherCountries;
    
    // Populate filter dropdown
    sortedCountries.forEach(country => {
        const option = document.createElement('option');
        option.value = country.code;
        option.textContent = `${country.flag} ${country.name}`;
        elements.countryFilter.appendChild(option);
    });
    
    // Also populate signup country dropdown with all countries (no Global option for signup)
    const signupCountryDropdown = document.getElementById('signupCountry');
    if (signupCountryDropdown) {
        signupCountryDropdown.innerHTML = '<option value="">🌍 Select your country...</option>';
        const signupCountries = countries.filter(c => c.code !== '').sort((a, b) => a.name.localeCompare(b.name));
        signupCountries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.name;
            option.textContent = `${country.flag} ${country.name}`;
            signupCountryDropdown.appendChild(option);
        });
    }
    
    console.log(`✅ Populated ${sortedCountries.length} countries in filter dropdown`);
}

// ===== TITLE UPDATE HELPER =====
function updateSectionTitle() {
    // Build title based on current filters
    let title = 'Trending News';
    
    if (currentFilters.mode === 'interest' && currentUser?.interests) {
        title = `News Based on Your Interests (${currentUser.interests.join(', ')})`;
    } else if (currentFilters.mode === 'userCountry' && currentFilters.country) {
        const country = availableCountries.find(c => c.code === currentFilters.country);
        if (country) {
            title = `News from ${country.name} ${country.flag}`;
        }
    } else if (currentFilters.country || currentFilters.category) {
        const parts = [];
        
        if (currentFilters.country) {
            const country = availableCountries.find(c => c.code === currentFilters.country);
            if (country) {
                parts.push(`${country.flag} ${country.name}`);
            }
        }
        
        if (currentFilters.category) {
            const categoryEmojis = {
                technology: '💻',
                business: '💼',
                sports: '⚽',
                health: '❤️',
                entertainment: '🎬',
                science: '🔬'
            };
            const emoji = categoryEmojis[currentFilters.category] || '📰';
            parts.push(`${emoji} ${currentFilters.category.charAt(0).toUpperCase() + currentFilters.category.slice(1)}`);
        }
        
        if (parts.length > 0) {
            title = `News: ${parts.join(' • ')}`;
        }
    }
    
    elements.sectionTitle.textContent = title;
}

// ===== FILTER FUNCTIONS =====
function filterTrending() {
    setActiveFilterButton('trendingBtn');
    currentFilters.mode = 'trending';
    currentFilters.country = '';
    currentFilters.category = '';
    elements.countryFilter.value = '';
    elements.categoryFilter.value = '';
    elements.countryFilter.classList.remove('active');
    elements.categoryFilter.classList.remove('active');
    updateSectionTitle();
    fetchMLEnhancedNews();
}

function filterByInterest() {
    if (!currentUser || !currentUser.interests || currentUser.interests.length === 0) {
        showToast('Please set your interests during signup first', 'error');
        return;
    }
    
    setActiveFilterButton('interestBtn');
    currentFilters.mode = 'interest';
    
    // Fetch news for ALL user interests combined
    currentFilters.category = ''; // Clear category filter
    elements.categoryFilter.value = '';
    elements.categoryFilter.classList.remove('active');
    elements.countryFilter.classList.remove('active');
    
    updateSectionTitle();
    
    // Fetch news for user's interests
    fetchNewsForUserInterests();
}

function filterByUserCountry() {
    if (!currentUser || !currentUser.country) {
        showToast('Please set your country during signup first', 'error');
        return;
    }
    
    setActiveFilterButton('countryBtn');
    currentFilters.mode = 'userCountry';
    
    // Find country code from user's country name
    const userCountry = availableCountries.find(c => 
        c.name.toLowerCase() === currentUser.country.toLowerCase()
    );
    
    if (userCountry) {
        currentFilters.country = userCountry.code;
        elements.countryFilter.value = userCountry.code;
        currentFilters.category = ''; // Clear category
        elements.categoryFilter.value = '';
        updateSectionTitle();
        fetchMLEnhancedNews();
    } else {
        showToast('Your country is not available in the supported list', 'error');
    }
}

// New function to fetch news based on user's interests
async function fetchNewsForUserInterests() {
    if (!currentUser || !currentUser.interests || currentUser.interests.length === 0) {
        showToast('No interests found', 'error');
        return;
    }
    
    // Reset article tracking for new session
    elements.newsGrid.innerHTML = '';
    resetArticleTracking();
    
    showLoading();
    hideError();
    hideNoResults();
    
    try {
        const token = localStorage.getItem('token');
        
        // Fetch news for each interest category
        const newsPromises = currentUser.interests.map(interest => {
            const params = new URLSearchParams();
            params.append('category', interest);
            params.append('sortBy', 'publishedAt');
            
            return fetch(`${API_BASE_URL}/api/news?${params}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            }).then(res => res.json());
        });
        
        const results = await Promise.all(newsPromises);
        
        // Combine all articles from different interests
        let allArticles = [];
        results.forEach(result => {
            if (result.status === 'success' && result.articles) {
                allArticles = allArticles.concat(result.articles);
            }
        });
        
        // Remove duplicates based on URL using global deduplication
        const uniqueArticles = allArticles.filter(article => isArticleUnique(article));
        
        // Shuffle and limit to 30 articles for variety
        const shuffled = uniqueArticles.sort(() => Math.random() - 0.5);
        const limitedArticles = shuffled.slice(0, 30);
        
        hideLoading();
        
        if (limitedArticles.length > 0) {
            console.log(`✅ Received ${limitedArticles.length} articles for user interests (deduplicated from ${allArticles.length})`);
            newsCache = limitedArticles;
            displayNews(limitedArticles);
        } else {
            showNoResults();
        }
        
    } catch (error) {
        hideLoading();
        showErrorMessage('Unable to fetch news for your interests');
        console.error('Fetch interests news error:', error);
    }
}

function setActiveFilterButton(buttonId) {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (buttonId) {
        document.getElementById(buttonId)?.classList.add('active');
    }
}

function updateActiveFilters() {
    const tags = [];
    
    // Show active filters based on mode
    if (currentFilters.mode === 'interest' && currentUser && currentUser.interests) {
        const categoryEmojis = {
            technology: '💻',
            business: '💼',
            sports: '⚽',
            health: '❤️',
            entertainment: '🎬',
            science: '🔬'
        };
        
        currentUser.interests.forEach(interest => {
            const emoji = categoryEmojis[interest] || '📰';
            tags.push({ 
                label: `${emoji} ${interest.charAt(0).toUpperCase() + interest.slice(1)}`, 
                type: 'interest',
                value: interest
            });
        });
    } else if (currentFilters.mode === 'userCountry' && currentFilters.country) {
        const country = availableCountries.find(c => c.code === currentFilters.country);
        if (country) {
            tags.push({ label: `${country.flag} ${country.name}`, type: 'userCountry' });
        }
    } else {
        // Regular filters
        if (currentFilters.country) {
            const country = availableCountries.find(c => c.code === currentFilters.country);
            if (country) {
                tags.push({ label: `${country.flag} ${country.name}`, type: 'country' });
            }
        }
        
        if (currentFilters.category) {
            const categoryEmojis = {
                technology: '💻',
                business: '💼',
                sports: '⚽',
                health: '❤️',
                entertainment: '🎬',
                science: '🔬'
            };
            const emoji = categoryEmojis[currentFilters.category] || '📰';
            tags.push({ 
                label: `${emoji} ${currentFilters.category.charAt(0).toUpperCase() + currentFilters.category.slice(1)}`, 
                type: 'category' 
            });
        }
    }
    
    if (tags.length > 0) {
        elements.activeFilterTags.innerHTML = tags.map(tag => 
            `<span class="filter-tag">
                ${tag.label}
                ${tag.type !== 'interest' && tag.type !== 'userCountry' ? 
                    `<button onclick="removeFilter('${tag.type}')" aria-label="Remove filter">
                        <i class="fas fa-times"></i>
                    </button>` : ''
                }
            </span>`
        ).join('');
        elements.activeFilters.classList.remove('hidden');
    } else {
        elements.activeFilters.classList.add('hidden');
    }
}

function removeFilter(type) {
    if (type === 'country') {
        currentFilters.country = '';
        elements.countryFilter.value = '';
    } else if (type === 'category') {
        currentFilters.category = '';
        elements.categoryFilter.value = '';
    }
    
    updateActiveFilters();
    fetchMLEnhancedNews();
}

function clearAllFilters() {
    currentFilters.country = '';
    currentFilters.category = '';
    currentFilters.mode = 'trending';
    elements.countryFilter.value = '';
    elements.categoryFilter.value = '';
    setActiveFilterButton('trendingBtn');
    elements.sectionTitle.textContent = 'Trending News';
    updateActiveFilters();
    fetchMLEnhancedNews();
}

function retryFetchNews() {
    fetchMLEnhancedNews();
}

// ===== AUTHENTICATION =====
function checkAuth() {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
        try {
            currentUser = JSON.parse(user);
            showMainApp();
        } catch (e) {
            console.error('Failed to parse user data:', e);
            showWelcomeScreen();
        }
    } else {
        showWelcomeScreen();
    }
}

async function handleLogin(event) {
    if (event) event.preventDefault();
    
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');
    
    if (!email || !password) {
        showError(errorEl, 'Please fill in all fields');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            localStorage.setItem('token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));
            currentUser = data.user;
            hideModals();
            showMainApp();
            showToast('Welcome back!', 'success');
        } else {
            showError(errorEl, data.message || 'Login failed');
        }
    } catch (error) {
        showError(errorEl, 'Unable to connect to server');
        console.error('Login error:', error);
    }
}

function goToStep2(event) {
    if (event) event.preventDefault();
    
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const errorEl = document.getElementById('signupError1');
    
    if (!name || !email || !password) {
        showError(errorEl, 'Please fill in all fields');
        return;
    }
    
    if (password.length < 6) {
        showError(errorEl, 'Password must be at least 6 characters');
        return;
    }
    
    errorEl.classList.add('hidden');
    document.getElementById('signupStep1').classList.add('hidden');
    document.getElementById('signupStep2').classList.remove('hidden');
}

function goToStep1() {
    document.getElementById('signupStep2').classList.add('hidden');
    document.getElementById('signupStep1').classList.remove('hidden');
}

async function handleSignup(event) {
    if (event) event.preventDefault();
    
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const country = document.getElementById('signupCountry').value.trim();
    const errorEl = document.getElementById('signupError2');
    const countryErrorEl = document.getElementById('countryError');
    
    const interests = Array.from(document.querySelectorAll('input[name="interest"]:checked'))
        .map(cb => cb.value);
    
    // Validate interests
    if (interests.length === 0) {
        showError(errorEl, 'Please select at least one interest');
        return;
    }
    
    // Validate country - REQUIRED and must be supported
    if (!country) {
        if (countryErrorEl) {
            countryErrorEl.textContent = '❌ Country selection is required';
            countryErrorEl.classList.remove('hidden');
        }
        showError(errorEl, 'Please select your country');
        return;
    }
    
    // Validate country against supported list
    const isCountrySupported = availableCountries.some(c => 
        c.name.toLowerCase() === country.toLowerCase()
    );
    
    if (!isCountrySupported) {
        if (countryErrorEl) {
            countryErrorEl.textContent = '❌ This country is not supported yet';
            countryErrorEl.classList.remove('hidden');
        }
        showError(errorEl, 'Your country is not in our supported list');
        return;
    }
    
    // Clear country error if validation passed
    if (countryErrorEl) {
        countryErrorEl.classList.add('hidden');
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name, 
                email, 
                password, 
                interests,
                country: country,
                state: null
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast('Account created successfully!', 'success');
            hideModals();
            setTimeout(() => showLogin(), 300);
        } else {
            showError(errorEl, data.message || 'Signup failed');
        }
    } catch (error) {
        showError(errorEl, 'Unable to connect to server');
        console.error('Signup error:', error);
    }
}

function logout() {
    const token = localStorage.getItem('token');
    if (token) {
        fetch(`${API_BASE_URL}/api/auth/logout`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        }).catch(err => console.error('Logout error:', err));
    }
    
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    currentUser = null;
    showWelcomeScreen();
    hideModals();
    showToast('Logged out successfully', 'success');
}

// ===== UI FUNCTIONS =====
function showMainApp() {
    elements.welcomeScreen.classList.add('hidden');
    elements.mainContent.classList.remove('hidden');
    elements.navBeforeLogin.classList.add('hidden');
    elements.navAfterLogin.classList.remove('hidden');
    elements.userName.textContent = currentUser.name;
    
    // Auto-select and display user's country
    if (currentUser && currentUser.country) {
        const userCountry = availableCountries.find(c => 
            c.name.toLowerCase() === currentUser.country.toLowerCase()
        );
        if (userCountry) {
            // Update dynamic country display in button
            const userCountryDisplay = document.getElementById('userCountryDisplay');
            if (userCountryDisplay) {
                userCountryDisplay.textContent = `${userCountry.flag} ${userCountry.name}`;
                userCountryDisplay.title = `Your selected country: ${userCountry.name}`;
            }
            
            // Set country filter and mode
            currentFilters.country = userCountry.code;
            elements.countryFilter.value = userCountry.code;
            elements.countryFilter.classList.add('active');
            currentFilters.mode = 'userCountry';
            
            console.log(`✅ Auto-selected country: ${userCountry.name} (${userCountry.flag})`);
        } else {
            console.warn(`⚠️ User country "${currentUser.country}" not found in supported countries list`);
        }
    } else {
        console.log('ℹ️ User has no country set');
    }
    
    fetchMLEnhancedNews();
    setupInfiniteScroll();
}

function showWelcomeScreen() {
    elements.welcomeScreen.classList.remove('hidden');
    elements.mainContent.classList.add('hidden');
    elements.navBeforeLogin.classList.remove('hidden');
    elements.navAfterLogin.classList.add('hidden');
}

function showLogin() {
    hideModals();
    elements.loginModal.classList.remove('hidden');
    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';
    document.getElementById('loginError').classList.add('hidden');
    document.getElementById('loginEmail').focus();
}

function showSignup() {
    hideModals();
    elements.signupModal.classList.remove('hidden');
    goToStep1();
    
    // Clear form
    document.getElementById('signupName').value = '';
    document.getElementById('signupEmail').value = '';
    document.getElementById('signupPassword').value = '';
    document.getElementById('signupCountry').value = '';
    document.getElementById('signupState').value = '';
    document.querySelectorAll('input[name="interest"]').forEach(cb => cb.checked = false);
    document.getElementById('signupError1').classList.add('hidden');
    document.getElementById('signupError2').classList.add('hidden');
    document.getElementById('signupName').focus();
}

function hideModals() {
    elements.loginModal.classList.add('hidden');
    elements.signupModal.classList.add('hidden');
}

function showError(element, message) {
    element.textContent = message;
    element.classList.remove('hidden');
}

function showToast(message, type = 'success') {
    elements.toastMessage.textContent = message;
    elements.toast.className = `toast ${type}`;
    elements.toast.classList.remove('hidden');
    
    setTimeout(() => {
        elements.toast.classList.add('hidden');
    }, 3000);
}

function showProfile() {
    showToast('Profile feature coming soon!', 'info');
    elements.dropdownMenu.classList.add('hidden');
}

function showSavedArticles() {
    showToast('Saved articles feature coming soon!', 'info');
    elements.dropdownMenu.classList.add('hidden');
}

// ===== ML-ENHANCED NEWS FETCHING =====
async function fetchMLEnhancedNews(pageNumber = 1) {
    // Reset pagination and article tracking if it's a new filter
    if (pageNumber === 1) {
        currentPage = 1;
        totalNewsLoaded = 0;
        hasMoreNews = true;
        nextPageToken = null;  // Reset pagination token for new request
        newsCache = [];  // Clear article cache for new filter
        elements.newsGrid.innerHTML = '';
        resetArticleTracking();  // Clear article tracking for new search
    }
    
    console.log(`🤖 Fetching ML-enhanced news (Page ${pageNumber})`);
    console.log(`📋 Current Mode: ${currentFilters.mode}`);
    console.log(`🔍 Filters - Country: ${currentFilters.country || 'All'}, Category: ${currentFilters.category || 'All'}`);
    
    // Show loading only for first page
    if (pageNumber === 1) {
        showLoading();
        hideError();
        hideNoResults();
    }
    
    try {
        const token = localStorage.getItem('token');
        const params = new URLSearchParams();
        
        // Smart News Loading Logic
        // Case 1: Default Load (just logged in, no custom filter)
        if (currentFilters.mode === 'trending') {
            console.log('📰 Case 1: Trending Mode');
            params.append('sortBy', currentFilters.sortBy);
        }
        // Case 2: User Selects Country + Category
        else if (currentFilters.country || currentFilters.category) {
            console.log('📰 Case 2: Custom Country/Category Filter');
            if (currentFilters.country) {
                params.append('country', currentFilters.country);
            }
            if (currentFilters.category) {
                params.append('category', currentFilters.category);
            }
            params.append('sortBy', currentFilters.sortBy);
        }
        // Case 3: User's Interest-based
        else if (currentFilters.mode === 'interest') {
            console.log('📰 Case 3: Interest-based Load');
            // Handled separately in fetchNewsForUserInterests
            return;
        }
        
        // Add pagination - use nextPageToken if available (pagination continuation)
        if (pageNumber > 1 && nextPageToken) {
            params.append('nextPage', nextPageToken);
            console.log(`📄 Using pagination token: ${nextPageToken.substring(0, 30)}...`);
        }
        
        console.log('📡 API Request:', `${API_BASE_URL}/api/news?${params}`);
        
        const response = await fetch(`${API_BASE_URL}/api/news?${params}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        const data = await response.json();
        console.log('📥 API Response received:', data);
        
        if (pageNumber === 1) {
            hideLoading();
        }
        
        if (data.status === 'success') {
            const articles = data.articles || [];
            console.log(`✅ Received ${articles.length} ML-processed articles`);
            console.log(`📌 Response country: ${data.country}, category: ${data.category}`);
            
            // Log first article details for debugging
            if (articles.length > 0) {
                console.log('📄 First article sample:', {
                    title: articles[0].title?.substring(0, 50),
                    source: articles[0].source?.name || 'Unknown',
                    country: articles[0].country,
                    hasImage: !!(articles[0].urlToImage || articles[0].image_url || articles[0].image),
                    hasUrl: !!(articles[0].url || articles[0].link),
                    publishDate: articles[0].publishedAt || articles[0].pubDate
                });
                
                // Show country breakdown of first 3 articles
                console.log('📍 First 3 articles country sources:');
                articles.slice(0, 3).forEach((art, idx) => {
                    console.log(`  ${idx + 1}. ${art.source?.name} | Country: ${art.country || 'N/A'} | ${art.title?.substring(0, 40)}`);
                });
            }
            
            // Update nextPage token for infinite scroll
            if (data.nextPage) {
                nextPageToken = data.nextPage;
                console.log(`📄 Next page available: ${nextPageToken.substring(0, 30)}...`);
            } else {
                nextPageToken = null;
            }
            
            if (pageNumber === 1) {
                // Reset cache and session for new search
                newsCache = articles;
                displayNews(articles);
                
                // Determine if more pages available
                hasMoreNews = articles.length === ARTICLES_PER_PAGE && !!nextPageToken;
                console.log(`📄 Pagination state: ${hasMoreNews ? 'More pages available' : 'No more pages'}`);
            } else {
                // For pagination: append unique articles that haven't been displayed
                appendNews(articles);
                
                // Update pagination state:
                // More news is available if we got a full page AND there's a next token
                const newArticlesAfterDedup = articles.filter(article => isArticleUnique(article)).length;
                hasMoreNews = articles.length === ARTICLES_PER_PAGE && !!nextPageToken;
                
                console.log(`📄 Pagination: Received ${articles.length}, kept ${newArticlesAfterDedup} after dedup. More pages: ${hasMoreNews}`);
                
                // If all articles were duplicates but more pages exist, user can keep scrolling
                if (newArticlesAfterDedup === 0 && hasMoreNews) {
                    console.log('⚠️ All pagination results were duplicates, but more pages available - will fetch on next scroll');
                }
            }
            
            totalNewsLoaded += articles.length;
            
            if (data.ml_enhanced) {
                console.log('🎯 Articles ranked by ML recommendation engine');
            }
            
            if (articles.length === 0 && pageNumber === 1) {
                console.warn('⚠️ No articles returned by API');
                showNoResults();
            }
        } else {
            console.error('❌ API Error:', data.message || 'Unknown error');
            if (pageNumber === 1) {
                showErrorMessage(data.message || 'Failed to fetch news');
            }
        }
    } catch (error) {
        hideLoading();
        if (pageNumber === 1) {
            showErrorMessage('Unable to connect to server. Please check your connection and try again.');
        }
        console.error('Fetch news error:', error);
    }
}

function displayNews(articles) {
    elements.newsGrid.innerHTML = '';
    
    if (!articles || articles.length === 0) {
        console.warn('⚠️ No articles to display');
        showNoResults();
        return;
    }
    
    // Deduplicate articles: filter out any we've already shown
    const uniqueArticles = articles.filter(article => isArticleUnique(article));
    
    console.log(`📰 Displaying ${uniqueArticles.length} unique articles (deduplicated from ${articles.length}, ${articles.length - uniqueArticles.length} duplicates filtered)`);
    
    if (uniqueArticles.length === 0) {
        console.warn('⚠️ All articles were duplicates - showing nothing');
        showNoResults();
        return;
    }
    
    let displayedCount = 0;
    uniqueArticles.forEach((article, index) => {
        // Check for image field (API might return image, urlToImage, or image_url from NewsData.io)
        const imageUrl = article.urlToImage || article.image || article.image_url;
        
        if (!imageUrl) {
            console.warn(`⚠️ Article ${index} skipped - no image URL:`, article.title?.substring(0, 50));
            return;
        }
        
        try {
            const card = createNewsCard(article);
            elements.newsGrid.appendChild(card);
            markArticleAsLoaded(article);  // Mark as displayed
            displayedCount++;
        } catch (error) {
            console.error(`❌ Error creating card for article ${index}:`, error, article);
        }
    });
    
    console.log(`✅ Successfully created ${displayedCount} news cards out of ${uniqueArticles.length} articles`);
    
    if (displayedCount === 0) {
        console.error('❌ No articles could be displayed - check image URLs');
        showNoResults();
    }
}

function appendNews(articles) {
    if (!articles || articles.length === 0) {
        console.warn('⚠️ No articles to append');
        return;
    }
    
    // Filter out duplicates using global tracking
    const newArticles = articles.filter(article => isArticleUnique(article));
    
    console.log(`📰 Appending ${newArticles.length} new articles (filtered from ${articles.length}, ${articles.length - newArticles.length} duplicates removed)`);
    
    if (newArticles.length === 0) {
        console.warn('⚠️ All pagination results were duplicates - skipping silently');
        return;
    }
    
    let appendedCount = 0;
    newArticles.forEach((article, index) => {
        const imageUrl = article.urlToImage || article.image || article.image_url;
        
        if (!imageUrl) {
            console.warn(`⚠️ Article skipped during append - no image URL`);
            return;
        }
        
        try {
            const card = createNewsCard(article);
            elements.newsGrid.appendChild(card);
            markArticleAsLoaded(article);  // Mark as displayed
            appendedCount++;
        } catch (error) {
            console.error(`❌ Error appending article:`, error);
        }
    });
    
    console.log(`✅ Appended ${appendedCount} news cards`);
}

// ===== PAGINATION & SCROLL =====
// Setup infinite scroll with pagination safety
function setupInfiniteScroll() {
    if (window.infiniteScrollListener) {
        window.removeEventListener('scroll', window.infiniteScrollListener);
    }
    
    window.infiniteScrollListener = () => {
        // Pagination safety checks:
        // 1. Don't fetch while already loading
        // 2. Don't fetch if no more news available
        // 3. Don't fetch on duplicate pages
        if (isLoadingMore || !hasMoreNews) return;
        
        const scrollPosition = window.innerHeight + window.scrollY;
        const pageBottom = document.documentElement.scrollHeight - 500; // Load when 500px from bottom
        
        if (scrollPosition >= pageBottom) {
            // Set loading flag BEFORE incrementing page to prevent duplicate fetches
            isLoadingMore = true;
            currentPage++;
            console.log(`📄 Loading page ${currentPage}... (Pagination safety: preventing duplicate fetches)`);
            
            // Fetch with error handling to ensure flag is reset
            fetchMLEnhancedNews(currentPage).catch(err => {
                console.error('❌ Pagination fetch failed:', err);
            }).finally(() => {
                // IMPORTANT: Reset flag after fetch completes to allow next pagination
                isLoadingMore = false;
            });
        }
    };
    
    window.addEventListener('scroll', window.infiniteScrollListener);
}

function createNewsCard(article) {
    if (!article || !article.title) {
        console.error('❌ Invalid article object - missing title');
        return null;
    }
    
    const card = document.createElement('div');
    card.className = 'news-card';
    
    // Store article URL as data attribute for deduplication in appendNews()
    const articleUrl = article.url || article.link;
    if (articleUrl) {
        card.setAttribute('data-article-url', articleUrl);
    }
    
    card.onclick = () => {
        trackArticleInteraction(article);
        if (article.url) {
            window.open(article.url, '_blank');
        } else {
            console.warn('⚠️ Article has no URL');
        }
    };
    
    // Safe date formatting
    let dateStr = 'Unknown date';
    try {
        const publishDate = article.publishedAt || article.pubDate;
        if (publishDate) {
            const date = new Date(publishDate);
            if (!isNaN(date.getTime())) {
                dateStr = date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric'
                });
            }
        }
    } catch (e) {
        console.warn('⚠️ Error formatting date:', e);
    }
    
    // Safe virality badge
    const viralityBadge = (article.virality_score && article.virality_score > 0.7) 
        ? `<div class="virality-badge">🔥 Trending (${(article.virality_score * 100).toFixed(0)}%)</div>` 
        : '';
    
    // Safe ML badge
    const mlBadge = article.ml_processed 
        ? '<span class="ml-badge">🤖 AI</span>' 
        : '';
    
    // Get image URL with fallback (handles NewsData.io 'image_url' field too)
    const imageUrl = article.urlToImage || article.image || article.image_url || 'https://via.placeholder.com/400x300?text=News';
    
    // Safe source name
    const sourceName = article.source?.name || 'News Source';
    
    // Safe description
    const description = article.description || article.summary || 'No description available.';
    
    card.innerHTML = `
        <div class="news-card-image-wrapper">
            <img 
                src="${imageUrl}" 
                alt="${escapeHtml(article.title.substring(0, 100))}"
                class="news-card-image"
                loading="lazy"
                onerror="this.onerror=null; this.src='https://via.placeholder.com/400x300?text=No+Image'; console.error('Failed to load image:', '${imageUrl}');"
            >
            <div class="news-card-overlay"></div>
            ${viralityBadge}
        </div>
        <div class="news-card-content">
            <div class="news-card-meta">
                <span class="news-card-source">${escapeHtml(sourceName)}</span>
                ${mlBadge}
                <span class="news-card-date">${dateStr}</span>
            </div>
            <h3 class="news-card-title">${escapeHtml(article.title)}</h3>
            <p class="news-card-description">${escapeHtml(description.substring(0, 150))}</p>
            <div class="news-card-read-more">
                Read More <i class="fas fa-chevron-right"></i>
            </div>
        </div>
    `;
    
    return card;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===== ARTICLE INTERACTION TRACKING =====
async function trackArticleInteraction(article) {
    console.log('📊 Tracking interaction:', article.title);
    
    const token = localStorage.getItem('token');
    if (!token) return;
    
    const interaction = {
        article_url: article.url,
        article_title: article.title,
        category: currentFilters.category || 'general',
        duration_seconds: Math.floor(Math.random() * 300) + 60
    };
    
    try {
        await fetch(`${API_BASE_URL}/api/articles/track-interaction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(interaction)
        });
        
        console.log('✅ Interaction tracked');
    } catch (error) {
        console.error('Failed to track interaction:', error);
    }
}

// ===== LOADING & ERROR STATES =====
function showLoading() {
    elements.loadingSpinner.classList.remove('hidden');
    elements.newsGrid.innerHTML = '';
}

function hideLoading() {
    elements.loadingSpinner.classList.add('hidden');
}

function showErrorMessage(message) {
    document.getElementById('errorText').textContent = message;
    elements.errorMessage.classList.remove('hidden');
}

function hideError() {
    elements.errorMessage.classList.add('hidden');
}

function showNoResults() {
    elements.noResults.classList.remove('hidden');
}

function hideNoResults() {
    elements.noResults.classList.add('hidden');
}

// ===== THEME =====
function initTheme() {
    const theme = localStorage.getItem('theme');
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        updateThemeIcons(true);
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const isDark = document.body.classList.contains('dark-mode');
    updateThemeIcons(isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
}

function updateThemeIcons(isDark) {
    const icon = isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    
    if (elements.themeToggle) {
        elements.themeToggle.innerHTML = icon;
    }
    if (elements.themeToggleBeforeLogin) {
        elements.themeToggleBeforeLogin.innerHTML = icon;
    }
}

// ===== START APP =====
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}