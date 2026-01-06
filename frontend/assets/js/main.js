/* Main Application Logic */

// Initialize App
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 App starting...');
    
    initializeApp();
    setupEventListeners();
    loadPageContent();
});

// App Initialization
async function initializeApp() {
    // Load stats
    await loadStats();
    
    // Load last updated time
    await loadLastUpdated();
    
    // Setup navbar
    setupNavbar();
}

// Load Stats
async function loadStats() {
    try {
        const statsContainer = DOM.byId('statsContainer');
        if (!statsContainer) return;

        const stats = await API.getStats();
        
        if (stats) {
            DOM.byId('totalJobs').textContent = Format.number(stats.total_jobs);
            DOM.byId('companiesHiring').textContent = Format.number(stats.companies_hiring);
            DOM.byId('locations').textContent = Format.number(stats.locations);
            DOM.byId('avgSalary').textContent = Format.currency(stats.average_salary);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        Alert.error('Failed to load statistics');
    }
}

// Load Last Updated Time
async function loadLastUpdated() {
    try {
        const lastUpdatedEl = DOM.byId('lastUpdated');
        if (!lastUpdatedEl) return;

        const lastUpdated = await API.getLastUpdated();
        lastUpdatedEl.textContent = `Last updated: ${lastUpdated}`;
    } catch (error) {
        console.error('Error loading last updated:', error);
    }
}

// Setup Navbar
function setupNavbar() {
    const navToggle = DOM.byId('navToggle');
    const navMenu = DOM.select('.navbar-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            DOM.toggleClass(navToggle, 'active');
            DOM.toggleClass(navMenu, 'active');
        });

        // Close menu on link click
        const navLinks = DOM.selectAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                DOM.removeClass(navToggle, 'active');
                DOM.removeClass(navMenu, 'active');
            });
        });
    }

    // Update active nav link
    updateActiveNavLink();
}

// Update Active Nav Link
function updateActiveNavLink() {
    const currentPath = window.location.pathname;
    const navLinks = DOM.selectAll('.nav-link');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            DOM.addClass(link, 'active');
        } else {
            DOM.removeClass(link, 'active');
        }
    });
}

// Setup Event Listeners
function setupEventListeners() {
    // Fetch Jobs Button
    const fetchJobsBtn = DOM.byId('fetchJobsBtn');
    if (fetchJobsBtn) {
        fetchJobsBtn.addEventListener('click', handleFetchJobs);
    }

    // Window resize - responsive handling
    window.addEventListener('resize', debounce(() => {
        console.log('Window resized');
    }, 300));
}

// Handle Fetch Jobs
async function handleFetchJobs() {
    const fetchJobsBtn = DOM.byId('fetchJobsBtn');
    const fetchStatus = DOM.byId('fetchStatus');
    
    if (!fetchJobsBtn || !fetchStatus) return;

    try {
        fetchJobsBtn.disabled = true;
        fetchJobsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';
        
        fetchStatus.innerHTML = '<div class="alert alert-info">⏳ Fetching fresh job data. This may take up to 3 minutes. Please do not refresh.</div>';

        const result = await API.fetchJobs();

        if (result.success) {
            fetchStatus.innerHTML = `<div class="alert alert-success">✅ ${result.message}</div>`;
            Alert.success(result.message);
            
            // Reload stats
            setTimeout(async () => {
                await loadStats();
                await loadLastUpdated();
            }, 2000);
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Error fetching jobs:', error);
        fetchStatus.innerHTML = `<div class="alert alert-error">❌ Error: ${error.message}</div>`;
        Alert.error('Failed to fetch jobs: ' + error.message);
    } finally {
        fetchJobsBtn.disabled = false;
        fetchJobsBtn.innerHTML = '<i class="fas fa-download"></i> Fetch Latest Jobs';
    }
}

// Load Page-Specific Content
async function loadPageContent() {
    const currentPath = window.location.pathname;
    
    console.log(`📄 Loading page: ${currentPath}`);

    switch (currentPath) {
        case '/':
            await loadHomePage();
            break;
        case '/recommendations':
            await loadRecommendationsPage();
            break;
        case '/dashboard':
            await loadDashboardPage();
            break;
        case '/saved-jobs':
            await loadSavedJobsPage();
            break;
    }
}

// Load Home Page
async function loadHomePage() {
    console.log('🏠 Loading home page');
}

// Load Recommendations Page
async function loadRecommendationsPage() {
    console.log('🎯 Loading recommendations page');
    
    // This will be implemented when we create recommendations.html
}

// Load Dashboard Page
async function loadDashboardPage() {
    console.log('📊 Loading dashboard page');
    
    // This will be implemented when we create market-dashboard.html
}

// Load Saved Jobs Page
async function loadSavedJobsPage() {
    console.log('💾 Loading saved jobs page');
    
    // This will be implemented when we create saved-jobs.html
}

// Export functions for use in other modules
window.API = API;
window.DOM = DOM;
window.Format = Format;
window.Storage = Storage;
window.Alert = Alert;
