/* Dashboard Page Logic */



// Chart instances
let companiesChart = null;
let locationsChart = null;
let salaryTrendsChart = null;
let skillsChart = null;
let trendsChart = null;
let experienceChart = null;
let rolesChart = null;

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

function initializeDashboard() {
    console.log('📊 Initializing dashboard');

    // Load location filter options
    loadLocationFilter();

    // Setup event listeners
    setupDashboardListeners();

    // Load initial data
    loadDashboardData();
}

// Load Location Filter
function loadLocationFilter() {
    const locationFilter = DOM.byId('locationFilter');
    
    LOCATIONS.forEach(location => {
        const option = DOM.create('option', { value: location }, location);
        locationFilter.appendChild(option);
    });
}

// Setup Listeners
function setupDashboardListeners() {
    const daysFilter = DOM.byId('daysFilter');
    const locationFilter = DOM.byId('locationFilter');
    const refreshBtn = DOM.byId('refreshDashboard');

    if (daysFilter) daysFilter.addEventListener('change', loadDashboardData);
    if (locationFilter) locationFilter.addEventListener('change', filterAndRender);
    if (refreshBtn) refreshBtn.addEventListener('click', loadDashboardData);
}

// Load Dashboard Data
async function loadDashboardData() {
    try {
        const days = DOM.byId('daysFilter').value;
        console.log('🔄 Loading dashboard data for', days || 'all', 'days');

        // Build query parameter - only add days if it has a value
        const daysParam = days ? `days=${days}` : '';
        const daysQuery = days ? { days } : {};

        // Fetch all analytics data in parallel
        const [
            jobs,
            summaryStats,
            topSkills,
            salaryTrends,
            locationStats,
            roleDistribution,
            experienceDistribution,
            postingTrends
        ] = await Promise.all([
            API.getJobs(1, 1000, daysQuery),
            fetch(`${API_BASE_URL}/api/summary-stats${daysParam ? '?' + daysParam : ''}`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/top-skills?${daysParam}${daysParam ? '&' : ''}top_n=15`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/salary-trends?${daysParam}${daysParam ? '&' : ''}group_by=location`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/location-stats${daysParam ? '?' + daysParam : ''}`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/role-distribution?${daysParam}${daysParam ? '&' : ''}top_n=10`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/experience-distribution${daysParam ? '?' + daysParam : ''}`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/posting-trends${daysParam ? '?' + daysParam : ''}`).then(r => r.json())
        ]);



        // Update metrics
        if (summaryStats && summaryStats.success && summaryStats.data) {
            const stats = summaryStats.data;
            DOM.byId('totalJobsMetric').textContent = (stats.total_jobs || 0).toLocaleString();
            DOM.byId('companiesMetric').textContent = (stats.total_companies || 0).toLocaleString();
            DOM.byId('locationsMetric').textContent = (stats.total_locations || 0).toLocaleString();
            if (stats.avg_salary > 0) {
                DOM.byId('avgSalaryMetric').textContent = '₹' + (stats.avg_salary / 100000).toFixed(2) + 'L';
            }
        }

        // Render charts
        if (salaryTrends && salaryTrends.success && salaryTrends.data) {
            renderSalaryTrendsChart(salaryTrends.data);
        }

        if (topSkills && topSkills.success && topSkills.data) {
            renderSkillsChart(topSkills.data);
        }

        if (locationStats && locationStats.success && locationStats.data) {
            renderLocationsChart(locationStats.data);
        }

        if (roleDistribution && roleDistribution.success && roleDistribution.data) {
            renderRolesChart(roleDistribution.data);
        }

        if (experienceDistribution && experienceDistribution.success && experienceDistribution.data) {
            renderExperienceChart(experienceDistribution.data);
        }

        if (postingTrends && postingTrends.success && postingTrends.data) {
            renderTrendsChart(postingTrends.data);
        }

        // Render companies chart from jobs data
        if (jobs && Array.isArray(jobs) && jobs.length > 0) {
            const companyCounts = {};
            jobs.forEach(job => {
                const company = job.company || 'Unknown';
                companyCounts[company] = (companyCounts[company] || 0) + 1;
            });
            renderCompaniesChart(companyCounts);
            renderTopCompaniesFromJobs(jobs);
            renderTopLocationsFromJobs(jobs);
        }

        // Update salary analytics from salary trends
        if (salaryTrends && salaryTrends.success && salaryTrends.data && salaryTrends.data.length > 0) {
            const salaries = salaryTrends.data.map(t => t['Average Salary']).filter(s => s > 0);
            if (salaries.length > 0) {
                const minSalary = Math.min(...salaries);
                const maxSalary = Math.max(...salaries);
                const avgSalary = salaries.reduce((a, b) => a + b) / salaries.length;
                
                DOM.byId('minSalary').textContent = '₹' + (minSalary / 100000).toFixed(2) + 'L';
                DOM.byId('avgSalary').textContent = '₹' + (avgSalary / 100000).toFixed(2) + 'L';
                DOM.byId('maxSalary').textContent = '₹' + (maxSalary / 100000).toFixed(2) + 'L';
            }
        }

    } catch (error) {
        console.error('Error loading dashboard data:', error);
        Alert.error('Failed to load dashboard data: ' + error.message);
    }
}

// Filter and Render
async function filterAndRender() {
    try {
        // Show loading spinner
        const spinner = DOM.byId('locationLoadingSpinner');
        if (spinner) spinner.style.display = 'block';
        
        const days = DOM.byId('daysFilter').value;
        const location = DOM.byId('locationFilter').value;
        
        console.log('🔍 Filtering dashboard for location:', location);
        
        // If "All" selected, load full data
        if (!location || location === 'All') {
            loadDashboardData();
            return;
        }
        
        // Fetch filtered data
        const [
            jobs,
            summaryStats,
            topSkills,
            salaryTrends,
            locationStats,
            roleDistribution,
            experienceDistribution,
            postingTrends
        ] = await Promise.all([
            API.getJobs(1, 1000, { days, location }),
            fetch(`${API_BASE_URL}/api/summary-stats?days=${days}&location=${location}`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/top-skills?days=${days}&location=${location}&top_n=15`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/salary-trends?days=${days}&location=${location}&group_by=title`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/location-stats?days=${days}&location=${location}`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/role-distribution?days=${days}&location=${location}&top_n=10`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/experience-distribution?days=${days}&location=${location}`).then(r => r.json()),
            fetch(`${API_BASE_URL}/api/posting-trends?days=${days}&location=${location}`).then(r => r.json())
        ]);
        
        // Update metrics
        if (summaryStats && summaryStats.success && summaryStats.data) {
            const stats = summaryStats.data;
            DOM.byId('totalJobsMetric').textContent = (stats.total_jobs || 0).toLocaleString();
            DOM.byId('companiesMetric').textContent = (stats.total_companies || 0).toLocaleString();
            DOM.byId('locationsMetric').textContent = (stats.total_locations || 0).toLocaleString();
            if (stats.avg_salary > 0) {
                DOM.byId('avgSalaryMetric').textContent = '₹' + (stats.avg_salary / 100000).toFixed(2) + 'L';
            }
        }
        
        // Render charts with filtered data
        if (salaryTrends && salaryTrends.success && salaryTrends.data) {
            renderSalaryTrendsChart(salaryTrends.data);
        }
        
        if (topSkills && topSkills.success && topSkills.data) {
            renderSkillsChart(topSkills.data);
        }
        
        if (roleDistribution && roleDistribution.success && roleDistribution.data) {
            renderRolesChart(roleDistribution.data);
        }
        
        if (experienceDistribution && experienceDistribution.success && experienceDistribution.data) {
            renderExperienceChart(experienceDistribution.data);
        }
        
        if (postingTrends && postingTrends.success && postingTrends.data) {
            renderTrendsChart(postingTrends.data);
        }
        
        // Render companies chart from jobs data
        if (jobs && Array.isArray(jobs) && jobs.length > 0) {
            const companyCounts = {};
            jobs.forEach(job => {
                const company = job.company || 'Unknown';
                companyCounts[company] = (companyCounts[company] || 0) + 1;
            });
            renderCompaniesChart(companyCounts);
        }
        
        console.log('✅ Dashboard filtered for:', location);
        
    } catch (error) {
        console.error('Error filtering dashboard:', error);
        Alert.error('Failed to filter dashboard: ' + error.message);
    } finally {
        // Hide loading spinner
        const spinner = DOM.byId('locationLoadingSpinner');
        if (spinner) spinner.style.display = 'none';
    }
}

// Render Companies Chart
function renderCompaniesChart(companies) {
    const ctx = DOM.byId('companiesChart');
    if (!ctx) return;

    // Handle both array and object formats
    let labels = [];
    let data = [];
    
    if (Array.isArray(companies)) {
        // If it's an array format
        labels = companies.slice(0, 10).map(c => c.company || c.name);
        data = companies.slice(0, 10).map(c => c.count || c.job_count);
    } else {
        // If it's an object/dict format
        labels = Object.keys(companies).slice(0, 10);
        data = Object.values(companies).slice(0, 10);
    }

    // Destroy existing chart if it exists
    if (companiesChart) {
        companiesChart.destroy();
    }

    companiesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Job Openings',
                data: data,
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4ecdc4',
                    '#45b7d1', '#ffd89b', '#ff6b9d', '#c44569', '#f8b195'
                ],
                borderColor: '#667eea',
                borderWidth: 1,
                borderRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false,
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)',
                    },
                },
                y: {
                    grid: {
                        display: false,
                    },
                },
            },
        },
    });
}

// Render Locations Chart
function renderLocationsChart(locations) {
    const ctx = DOM.byId('locationsChart');
    if (!ctx) return;

    // Handle both array and object formats
    let labels = [];
    let data = [];
    
    if (Array.isArray(locations)) {
        // If it's an array of objects from API
        labels = locations.slice(0, 8).map(loc => loc.location || loc.name);
        data = locations.slice(0, 8).map(loc => loc.job_count || loc.count);
    } else {
        // If it's an object/dict format
        labels = Object.keys(locations).slice(0, 8);
        data = Object.values(locations).slice(0, 8);
    }

    // Destroy existing chart if it exists
    if (locationsChart) {
        locationsChart.destroy();
    }

    locationsChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4ecdc4',
                    '#45b7d1', '#ffd89b', '#ff6b9d'
                ],
                borderColor: '#ffffff',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        font: {
                            size: 12,
                        },
                    },
                },
            },
        },
    });
}

// Render Top Companies from Jobs Data
function renderTopCompaniesFromJobs(jobs) {
    const container = DOM.byId('topCompaniesContainer');
    if (!container) return;
    
    container.innerHTML = '';

    if (!jobs || jobs.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No company data available</p>';
        return;
    }

    // Get top companies
    const companyCounts = {};
    jobs.forEach(job => {
        const company = job.company || 'Unknown';
        companyCounts[company] = (companyCounts[company] || 0) + 1;
    });

    Object.entries(companyCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .forEach(([company, count]) => {
            const companyCard = DOM.create('div', {
                style: 'padding: var(--spacing-lg); background: var(--bg-secondary); border-radius: var(--radius-md); border-left: 4px solid var(--primary-color);',
            });

            const name = DOM.create('h4', { style: 'margin: 0 0 var(--spacing-sm) 0;' }, company);
            const countEl = DOM.create('p', {
                style: 'margin: 0; color: var(--text-secondary); font-size: var(--text-sm);',
            }, `${count} open position${count !== 1 ? 's' : ''}`);

            companyCard.appendChild(name);
            companyCard.appendChild(countEl);
            container.appendChild(companyCard);
        });
}

// Render Top Locations from Jobs Data
function renderTopLocationsFromJobs(jobs) {
    const container = DOM.byId('topLocationsContainer');
    if (!container) return;
    
    container.innerHTML = '';

    if (!jobs || jobs.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary);">No location data available</p>';
        return;
    }

    // Get top locations
    const locationCounts = {};
    jobs.forEach(job => {
        const location = job.location || 'Unknown';
        locationCounts[location] = (locationCounts[location] || 0) + 1;
    });

    const topLocations = Object.entries(locationCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8);

    const list = DOM.create('div', { style: 'display: flex; flex-direction: column; gap: var(--spacing-md);' });

    topLocations.forEach(([location, count]) => {
        const total = Object.values(locationCounts).reduce((a, b) => a + b);
        const percentage = ((count / total) * 100).toFixed(1);

        const item = DOM.create('div', {
            style: 'display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-md); border-bottom: 1px solid var(--border-light);'
        });

        const locationName = DOM.create('span', {
            style: 'font-weight: var(--font-medium);'
        }, location);

        const stats = DOM.create('div', {
            style: 'display: flex; gap: var(--spacing-lg); text-align: right;'
        });

        const jobCount = DOM.create('span', {
            style: 'color: var(--primary-color); font-weight: var(--font-bold);'
        }, count);

        const bar = DOM.create('div', {
            style: `width: 100px; height: 8px; background: var(--border-light); border-radius: var(--radius-full); overflow: hidden;`
        });

        const barFill = DOM.create('div', {
            style: `width: ${percentage}%; height: 100%; background: linear-gradient(90deg, var(--primary-color), var(--accent-color)); border-radius: var(--radius-full);`
        });

        bar.appendChild(barFill);
        stats.appendChild(jobCount);
        stats.appendChild(bar);
        item.appendChild(locationName);
        item.appendChild(stats);
        list.appendChild(item);
    });

    container.appendChild(list);
}

// Render Salary Trends Chart
function renderSalaryTrendsChart(salaryTrends) {
    const ctx = DOM.byId('salaryTrendsChart');
    if (!ctx) return;

    const labels = salaryTrends.map(t => t.location);
    const data = salaryTrends.map(t => t['Average Salary']);

    if (salaryTrendsChart) {
        salaryTrendsChart.destroy();
    }

    salaryTrendsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Average Salary (₹)',
                data: data,
                backgroundColor: '#667eea',
                borderColor: '#5568d3',
                borderWidth: 1,
                borderRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                },
                y: {
                    grid: { display: false },
                },
            },
        },
    });
}

// Render Skills Chart
function renderSkillsChart(skills) {
    const ctx = DOM.byId('skillsChart');
    if (!ctx) return;

    const labels = skills.map(s => s.skill);
    const data = skills.map(s => s.count);

    if (skillsChart) {
        skillsChart.destroy();
    }

    skillsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Job Postings',
                data: data,
                backgroundColor: '#764ba2',
                borderColor: '#6a3f8f',
                borderWidth: 1,
                borderRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {
                legend: { display: false },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                },
                y: {
                    grid: { display: false },
                },
            },
        },
    });
}

// Render Trends Chart
function renderTrendsChart(trends) {
    const ctx = DOM.byId('trendsChart');
    if (!ctx) return;

    const labels = trends.map(t => t.date);
    const data = trends.map(t => t.count);

    if (trendsChart) {
        trendsChart.destroy();
    }

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Daily Job Postings',
                data: data,
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: true },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                },
            },
        },
    });
}

// Render Experience Chart
function renderExperienceChart(experienceData) {
    const ctx = DOM.byId('experienceChart');
    if (!ctx) return;

    const labels = experienceData.map(e => e.experience_level);
    const data = experienceData.map(e => e.count);

    if (experienceChart) {
        experienceChart.destroy();
    }

    experienceChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb'
                ],
                borderColor: '#ffffff',
                borderWidth: 2,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 20, font: { size: 12 } },
                },
            },
        },
    });
}

// Render Roles Chart
function renderRolesChart(roles) {
    const ctx = DOM.byId('rolesChart');
    if (!ctx) return;

    const labels = roles.map(r => r.role);
    const data = roles.map(r => r.count);

    if (rolesChart) {
        rolesChart.destroy();
    }

    rolesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Jobs',
                data: data,
                backgroundColor: [
                    '#667eea', '#764ba2', '#f093fb', '#f5576c', '#4ecdc4',
                    '#45b7d1', '#ffd89b', '#ff6b9d', '#c44569', '#f8b195'
                ],
                borderColor: '#667eea',
                borderWidth: 1,
                borderRadius: 5,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                },
            },
        },
    });
}
