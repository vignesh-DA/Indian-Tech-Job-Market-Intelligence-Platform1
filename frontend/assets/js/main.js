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
    // Check authentication and load user profile
    await checkAuth();
    
    // Load stats
    await loadStats();
    
    // Load last updated time
    await loadLastUpdated();
    
    // Check if scraping is in progress and resume polling
    await checkScrapingStatus();
    
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

// Check Scraping Status on Page Load
async function checkScrapingStatus() {
    try {
        const fetchStatus = DOM.byId('fetchStatus');
        const fetchJobsBtn = DOM.byId('fetchJobsBtn');
        if (!fetchStatus || !fetchJobsBtn) return;

        const statusResponse = await fetch('/api/fetch-jobs-status');
        const statusData = await statusResponse.json();
        
        if (statusData.success && statusData.status && statusData.status.is_running) {
            // Scraping is in progress - show status and resume polling
            const status = statusData.status;
            
            fetchJobsBtn.disabled = true;
            fetchJobsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scraping in Progress...';
            
            fetchStatus.innerHTML = `
                <div class="alert alert-info">
                    ⏳ ${status.message}
                    <div style="margin-top: 10px;">
                        <div style="background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #4CAF50, #8BC34A); height: 100%; width: ${status.progress}%; transition: width 0.5s;"></div>
                        </div>
                        <div style="text-align: center; margin-top: 5px; font-size: 14px;">${status.progress}% Complete</div>
                    </div>
                    <div style="margin-top: 10px; font-size: 13px; color: #666;">
                        💡 <strong>Tip:</strong> Scraping continues in the background. You can close this tab and come back later to see the results.
                    </div>
                </div>
            `;
            
            // Resume polling
            startStatusPolling();
        } else if (statusData.success && statusData.status) {
            // Not running - check if there's a completion message
            const status = statusData.status;
            if (status.progress === 100 && status.last_completed) {
                const completedDate = new Date(status.last_completed);
                const now = new Date();
                const diffMinutes = (now - completedDate) / (1000 * 60);
                
                // Show success message if completed within last 5 minutes
                if (diffMinutes < 5) {
                    fetchStatus.innerHTML = `<div class="alert alert-success">✅ ${status.message}</div>`;
                }
            }
        }
    } catch (error) {
        console.error('Error checking scraping status:', error);
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
        fetchJobsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting Scraper...';
        
        fetchStatus.innerHTML = `
            <div class="alert alert-info">
                ⏳ Initiating job scraper... This process runs in the background and may take 3-5 minutes.
                <div style="margin-top: 10px; font-size: 13px; color: #666;">
                    💡 <strong>Good news:</strong> You can close this tab! The scraping will continue, and data will be ready when you return.
                </div>
            </div>
        `;

        const result = await API.fetchJobs();

        if (result.success) {
            // Start polling for status updates
            startStatusPolling();
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        console.error('Error fetching jobs:', error);
        fetchStatus.innerHTML = `<div class="alert alert-error">❌ Error: ${error.message}</div>`;
        Alert.error('Failed to fetch jobs: ' + error.message);
        fetchJobsBtn.disabled = false;
        fetchJobsBtn.innerHTML = '<i class="fas fa-download"></i> Fetch Latest Jobs';
    }
}

// Start Status Polling (extracted for reuse)
let statusPollInterval = null;

function startStatusPolling() {
    // Clear any existing interval
    if (statusPollInterval) {
        clearInterval(statusPollInterval);
    }
    
    const fetchJobsBtn = DOM.byId('fetchJobsBtn');
    const fetchStatus = DOM.byId('fetchStatus');
    
    if (!fetchJobsBtn || !fetchStatus) return;
    
    let pollCount = 0;
    const maxPolls = 120; // Poll for up to 10 minutes (5 second intervals)
    
    statusPollInterval = setInterval(async () => {
        pollCount++;
        
        try {
            const statusResponse = await fetch('/api/fetch-jobs-status');
            const statusData = await statusResponse.json();
            
            if (statusData.success && statusData.status) {
                const status = statusData.status;
                
                if (status.is_running) {
                    // Show progress
                    fetchStatus.innerHTML = `
                        <div class="alert alert-info">
                            ⏳ ${status.message}
                            <div style="margin-top: 10px;">
                                <div style="background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #4CAF50, #8BC34A); height: 100%; width: ${status.progress}%; transition: width 0.5s;"></div>
                                </div>
                                <div style="text-align: center; margin-top: 5px; font-size: 14px;">${status.progress}% Complete</div>
                            </div>
                            <div style="margin-top: 10px; font-size: 13px; color: #666;">
                                💡 <strong>Tip:</strong> This runs in the background. Feel free to close this tab and return later!
                            </div>
                        </div>
                    `;
                } else {
                    // Job fetch completed
                    clearInterval(statusPollInterval);
                    statusPollInterval = null;
                    
                    if (status.progress === 100) {
                        fetchStatus.innerHTML = `
                            <div class="alert alert-success">
                                ✅ ${status.message}
                                <div style="margin-top: 8px; font-size: 14px;">
                                    🎉 <strong>Ready to explore!</strong> Check out the <a href="/dashboard" style="color: #4CAF50; text-decoration: underline;">Market Dashboard</a> for latest trends.
                                </div>
                            </div>
                        `;
                        Alert.success(status.message);
                    } else {
                        fetchStatus.innerHTML = `<div class="alert alert-error">❌ ${status.message}</div>`;
                        Alert.error(status.message);
                    }
                    
                    // Reload stats
                    setTimeout(async () => {
                        await loadStats();
                        await loadLastUpdated();
                        fetchJobsBtn.disabled = false;
                        fetchJobsBtn.innerHTML = '<i class="fas fa-download"></i> Fetch Latest Jobs';
                    }, 2000);
                }
            }
            
            // Stop polling after max attempts
            if (pollCount >= maxPolls) {
                clearInterval(statusPollInterval);
                statusPollInterval = null;
                fetchJobsBtn.disabled = false;
                fetchJobsBtn.innerHTML = '<i class="fas fa-download"></i> Fetch Latest Jobs';
                
                fetchStatus.innerHTML = `
                    <div class="alert alert-warning">
                        ⏰ Status check timed out. The scraping is still running in the background. Refresh the page in a few minutes to see results.
                    </div>
                `;
            }
        } catch (statusError) {
            console.error('Error polling status:', statusError);
        }
    }, 5000); // Poll every 5 seconds
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

// Check Authentication Status
async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/user`);
        const data = await response.json();
        
        if (data.authenticated) {
            // User is logged in - update profile picture
            const user = data.user;
            
            // Update navbar profile picture
            const profileImg = document.getElementById('profileImg');
            if (profileImg && user.picture) {
                profileImg.src = user.picture;
            }
            
            // Update dropdown profile picture
            const dropdownProfilePic = document.getElementById('dropdownProfilePic');
            if (dropdownProfilePic && user.picture) {
                dropdownProfilePic.src = user.picture;
            }
            
            // Update user info in dropdown
            const dropdownUserName = document.getElementById('dropdownUserName');
            if (dropdownUserName) {
                dropdownUserName.textContent = user.name || 'User';
            }
            
            const dropdownUserEmail = document.getElementById('dropdownUserEmail');
            if (dropdownUserEmail) {
                dropdownUserEmail.textContent = user.email || '';
            }
            
            // Setup profile dropdown toggle
            const profileBtn = document.getElementById('profileBtn');
            const profileDropdown = document.getElementById('profileDropdown');
            
            if (profileBtn && profileDropdown) {
                profileBtn.addEventListener('click', () => {
                    profileDropdown.classList.toggle('show');
                });
                
                // Close dropdown when clicking outside
                document.addEventListener('click', (e) => {
                    if (!profileDropdown.contains(e.target) && !profileBtn.contains(e.target)) {
                        profileDropdown.classList.remove('show');
                    }
                });
            }
            
            // Setup logout button
            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    try {
                        await fetch(`${API_BASE_URL}/api/auth/logout`, { method: 'POST' });
                        window.location.href = '/login';
                    } catch (error) {
                        console.error('Logout failed:', error);
                    }
                });
            }
        } else {
            // User not logged in - redirect to login
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        // Don't redirect on auth check failure (could be offline)
    }
}

// Export functions for use in other modules
window.API = API;
window.DOM = DOM;
window.Format = Format;
window.Storage = Storage;
window.Alert = Alert;
