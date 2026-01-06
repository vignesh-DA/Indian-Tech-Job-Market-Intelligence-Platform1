/* Profile and Saved Jobs Logic */

let savedJobs = [];
let filteredSavedJobs = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeProfilePage();
});

function initializeProfilePage() {
    console.log('💾 Initializing saved jobs page');

    // Load saved jobs
    loadSavedJobs();

    // Setup event listeners
    setupProfileListeners();
}

// Load Saved Jobs
function loadSavedJobs() {
    savedJobs = Storage.get(STORAGE_KEYS.SAVED_JOBS, []);

    if (savedJobs.length === 0) {
        renderEmptyState();
    } else {
        filteredSavedJobs = savedJobs;
        renderSavedJobs();
        DOM.byId('clearAllBtn').style.display = 'block';
    }
}

// Setup Event Listeners
function setupProfileListeners() {
    const searchInput = DOM.byId('searchInput');
    const statusFilter = DOM.byId('statusFilter');
    const filterBtn = DOM.byId('filterBtn');
    const clearAllBtn = DOM.byId('clearAllBtn');

    if (searchInput) {
        searchInput.addEventListener('keyup', debounce(filterJobs, 300));
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', filterJobs);
    }

    if (filterBtn) {
        filterBtn.addEventListener('click', filterJobs);
    }

    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', clearAllSavedJobs);
    }
}

// Filter Jobs
function filterJobs() {
    const searchTerm = DOM.byId('searchInput').value.toLowerCase();
    const status = DOM.byId('statusFilter').value;

    filteredSavedJobs = savedJobs.filter(job => {
        const matchesSearch =
            !searchTerm ||
            (job.title && job.title.toLowerCase().includes(searchTerm)) ||
            (job.company && job.company.toLowerCase().includes(searchTerm)) ||
            (job.location && job.location.toLowerCase().includes(searchTerm));

        const jobStatus = Storage.get(`jobStatus_${job.id}`, 'interested');
        const matchesStatus = !status || jobStatus === status;

        return matchesSearch && matchesStatus;
    });

    if (filteredSavedJobs.length === 0) {
        renderNoResults();
    } else {
        renderSavedJobs();
    }
}

// Render Saved Jobs
function renderSavedJobs() {
    const container = DOM.byId('savedJobsContainer');
    container.innerHTML = '';

    filteredSavedJobs.forEach((job, index) => {
        const jobStatus = Storage.get(`jobStatus_${job.id}`, 'interested');
        const applicationDate = Storage.get(`jobApplied_${job.id}`, null);

        const card = DOM.create('div', { className: 'card' });

        const header = DOM.create('div', { className: 'card-header' });
        const headerTitle = DOM.create('div', {
            style: 'display: flex; justify-content: space-between; align-items: start; gap: var(--spacing-md);',
        });

        const titleDiv = DOM.create('div', { style: 'flex: 1;' });
        const title = DOM.create('h3', { style: 'margin: 0;' }, job.title || 'Job Title');
        const company = DOM.create('p', {
            style: 'margin: var(--spacing-sm) 0 0 0; color: var(--text-secondary); font-size: var(--text-sm);',
        }, job.company || 'Company');
        titleDiv.appendChild(title);
        titleDiv.appendChild(company);

        const statusBadge = DOM.create('span', {
            className: `badge badge-${getStatusColor(jobStatus)}`,
        }, Format.capitalize(jobStatus));

        headerTitle.appendChild(titleDiv);
        headerTitle.appendChild(statusBadge);
        header.appendChild(headerTitle);

        const body = DOM.create('div', { className: 'card-body' });

        // Job Details
        const detailsGrid = DOM.create('div', {
            style: 'display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: var(--spacing-md); margin-bottom: var(--spacing-lg);',
        });

        // Location
        const locationEl = DOM.create('div');
        locationEl.innerHTML = `
            <p style="font-size: var(--text-xs); color: var(--text-secondary); margin-bottom: var(--spacing-xs); text-transform: uppercase; letter-spacing: 0.5px;">Location</p>
            <p style="font-weight: var(--font-semibold);">${job.location || 'Not specified'}</p>
        `;
        detailsGrid.appendChild(locationEl);

        // Salary
        const salaryEl = DOM.create('div');
        const salary = job.salary_max ? Format.currency(job.salary_max) : 'Not specified';
        salaryEl.innerHTML = `
            <p style="font-size: var(--text-xs); color: var(--text-secondary); margin-bottom: var(--spacing-xs); text-transform: uppercase; letter-spacing: 0.5px;">Salary</p>
            <p style="font-weight: var(--font-semibold);">${salary}</p>
        `;
        detailsGrid.appendChild(salaryEl);

        // Saved Date
        const savedDate = Storage.get(`jobSaved_${job.id}`, new Date().toISOString());
        const dateEl = DOM.create('div');
        dateEl.innerHTML = `
            <p style="font-size: var(--text-xs); color: var(--text-secondary); margin-bottom: var(--spacing-xs); text-transform: uppercase; letter-spacing: 0.5px;">Saved</p>
            <p style="font-weight: var(--font-semibold);">${Format.timeAgo(savedDate)}</p>
        `;
        detailsGrid.appendChild(dateEl);

        body.appendChild(detailsGrid);

        // Description
        if (job.description) {
            const desc = DOM.create('p', {
                style: 'color: var(--text-secondary); margin-bottom: var(--spacing-lg); font-size: var(--text-sm);',
            }, Format.truncate(job.description, 200));
            body.appendChild(desc);
        }

        // Status Selector
        const statusSection = DOM.create('div', {
            style: 'margin-bottom: var(--spacing-lg); padding: var(--spacing-md); background: var(--bg-secondary); border-radius: var(--radius-md);',
        });

        const statusLabel = DOM.create('p', {
            style: 'font-size: var(--text-sm); color: var(--text-secondary); margin-bottom: var(--spacing-sm); font-weight: var(--font-semibold);',
        }, 'Status');

        const statusButtons = DOM.create('div', {
            style: 'display: flex; gap: var(--spacing-sm); flex-wrap: wrap;',
        });

        ['interested', 'applied', 'rejected'].forEach(status => {
            const btn = DOM.create('button', {
                className: `btn btn-sm ${jobStatus === status ? 'btn-primary' : 'btn-secondary'}`,
                innerHTML: {
                    'interested': '<i class="fas fa-heart"></i> Interested',
                    'applied': '<i class="fas fa-check"></i> Applied',
                    'rejected': '<i class="fas fa-times"></i> Not Interested',
                }[status],
                onClick: () => updateJobStatus(job.id, status),
            });
            statusButtons.appendChild(btn);
        });

        statusSection.appendChild(statusLabel);
        statusSection.appendChild(statusButtons);
        body.appendChild(statusSection);

        const footer = DOM.create('div', { className: 'card-footer' });
        const footerContent = DOM.create('div', {
            style: 'display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--spacing-md);',
        });

        // Application Info
        if (applicationDate) {
            const appInfo = DOM.create('p', {
                style: 'margin: 0; font-size: var(--text-sm); color: var(--text-secondary);',
            }, `Applied on ${Format.date(applicationDate)}`);
            footerContent.appendChild(appInfo);
        } else {
            footerContent.appendChild(DOM.create('div'));
        }

        // Action Buttons
        const buttonsDiv = DOM.create('div', {
            style: 'display: flex; gap: var(--spacing-sm);',
        });

        const removeBtn = DOM.create('button', {
            className: 'btn btn-secondary btn-sm',
            innerHTML: '<i class="fas fa-trash"></i> Remove',
            onClick: () => removeSavedJob(job.id),
        });

        const viewBtn = DOM.create('a', {
            className: 'btn btn-primary btn-sm',
            href: job.url || '#',
            target: '_blank',
            innerHTML: '<i class="fas fa-external-link-alt"></i> View',
        });

        buttonsDiv.appendChild(removeBtn);
        buttonsDiv.appendChild(viewBtn);
        footerContent.appendChild(buttonsDiv);

        footer.appendChild(footerContent);

        card.appendChild(header);
        card.appendChild(body);
        card.appendChild(footer);

        container.appendChild(card);

        // Add spacing
        if (index < filteredSavedJobs.length - 1) {
            container.appendChild(DOM.create('div', { style: 'height: var(--spacing-md);' }));
        }
    });
}

// Render Empty State
function renderEmptyState() {
    const container = DOM.byId('savedJobsContainer');
    container.innerHTML = `
        <div style="text-align: center; padding: var(--spacing-3xl);">
            <i class="fas fa-inbox" style="font-size: var(--text-4xl); color: var(--text-light); margin-bottom: var(--spacing-lg); display: block;"></i>
            <h3>No saved jobs yet</h3>
            <p style="color: var(--text-secondary); margin-bottom: var(--spacing-lg);">
                Start exploring job recommendations and save jobs to track them here.
            </p>
            <a href="/recommendations" class="btn btn-primary">
                <i class="fas fa-search"></i> Find Jobs
            </a>
        </div>
    `;
}

// Render No Results
function renderNoResults() {
    const container = DOM.byId('savedJobsContainer');
    container.innerHTML = `
        <div style="text-align: center; padding: var(--spacing-3xl);">
            <i class="fas fa-search" style="font-size: var(--text-4xl); color: var(--text-light); margin-bottom: var(--spacing-lg); display: block;"></i>
            <h3>No jobs match your search</h3>
            <p style="color: var(--text-secondary);">Try adjusting your search or filter criteria.</p>
        </div>
    `;
}

// Update Job Status
function updateJobStatus(jobId, status) {
    Storage.set(`jobStatus_${jobId}`, status);

    if (status === 'applied') {
        Storage.set(`jobApplied_${jobId}`, new Date().toISOString());
    }

    Alert.success(`Status updated to ${Format.capitalize(status)}`);
    renderSavedJobs();
}

// Remove Saved Job
function removeSavedJob(jobId) {
    if (confirm('Are you sure you want to remove this job?')) {
        savedJobs = savedJobs.filter(job => job.id !== jobId);
        Storage.set(STORAGE_KEYS.SAVED_JOBS, savedJobs);

        // Remove related data
        Storage.remove(`jobStatus_${jobId}`);
        Storage.remove(`jobApplied_${jobId}`);
        Storage.remove(`jobSaved_${jobId}`);

        Alert.success('Job removed');

        if (savedJobs.length === 0) {
            DOM.byId('clearAllBtn').style.display = 'none';
            renderEmptyState();
        } else {
            filteredSavedJobs = filteredSavedJobs.filter(job => job.id !== jobId);
            if (filteredSavedJobs.length === 0) {
                renderNoResults();
            } else {
                renderSavedJobs();
            }
        }
    }
}

// Clear All Saved Jobs
function clearAllSavedJobs() {
    if (confirm('Are you sure you want to remove all saved jobs? This cannot be undone.')) {
        savedJobs = [];
        Storage.set(STORAGE_KEYS.SAVED_JOBS, []);
        DOM.byId('clearAllBtn').style.display = 'none';
        Alert.success('All jobs removed');
        renderEmptyState();
    }
}

// Get Status Color
function getStatusColor(status) {
    const colors = {
        'interested': 'primary',
        'applied': 'success',
        'rejected': 'danger',
    };
    return colors[status] || 'primary';
}
