/* Recommendations Page Logic */

let userSkills = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeRecommendationsPage();
});

function initializeRecommendationsPage() {
    console.log('🎯 Initializing recommendations page');

    // Load roles from API first
    loadRolesFromAPI().then(() => {
        // Load form options
        loadFormOptions();

        // Setup event listeners
        setupFormListeners();

        // Load saved profile if exists
        loadSavedProfile();
    }).catch(error => {
        console.warn('Failed to load roles from API, using fallback:', error);
        // Use fallback - just load form with empty roles
        loadFormOptions();
        setupFormListeners();
        loadSavedProfile();
    });
}

// Load roles from API
async function loadRolesFromAPI() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/roles`);
        const result = await response.json();
        
        if (result.success && Array.isArray(result.data)) {
            ROLES = result.data;
            console.log('✅ Loaded', ROLES.length, 'unique roles from database');
        }
    } catch (error) {
        console.warn('Could not load roles from API:', error);
    }
}

// Load Form Options
function loadFormOptions() {
    // Load roles
    const roleSelect = DOM.byId('roleSelect');
    if (roleSelect) {
        // Clear existing options except the first placeholder
        while (roleSelect.options.length > 1) {
            roleSelect.remove(1);
        }
        ROLES.forEach(role => {
            const option = DOM.create('option', { value: role }, role);
            roleSelect.appendChild(option);
        });
        console.log('✅ Roles loaded:', ROLES.length);
    } else {
        console.warn('⚠️ Role select element not found');
    }

    // Load experience levels
    const experienceSelect = DOM.byId('experienceSelect');
    if (experienceSelect) {
        // Clear existing options except the first placeholder
        while (experienceSelect.options.length > 1) {
            experienceSelect.remove(1);
        }
        EXPERIENCE_LEVELS.forEach(level => {
            const option = DOM.create('option', { value: level }, level);
            experienceSelect.appendChild(option);
        });
        console.log('✅ Experience levels loaded:', EXPERIENCE_LEVELS.length);
    } else {
        console.warn('⚠️ Experience select element not found');
    }

    // Load locations
    const locationSelect = DOM.byId('locationSelect');
    if (locationSelect) {
        // Clear existing options except the first placeholder
        while (locationSelect.options.length > 1) {
            locationSelect.remove(1);
        }
        LOCATIONS.forEach(location => {
            const option = DOM.create('option', { value: location }, location);
            locationSelect.appendChild(option);
        });
        console.log('✅ Locations loaded:', LOCATIONS.length);
    } else {
        console.warn('⚠️ Location select element not found');
    }
}

// Setup Form Listeners
function setupFormListeners() {
    const profileForm = DOM.byId('profileForm');
    const skillInput = DOM.byId('skillInput');
    const addSkillBtn = DOM.byId('addSkillBtn');
    const matchScoreFilter = DOM.byId('matchScoreFilter');
    const maxRecommendationsSlider = DOM.byId('maxRecommendationsSlider');
    const fetchJobsBtn = DOM.byId('fetchJobsBtn');

    // Add skill on Enter key or button click
    if (skillInput) {
        skillInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSkill();
            }
        });
    }

    // Add skill button click
    if (addSkillBtn) {
        addSkillBtn.addEventListener('click', function(e) {
            e.preventDefault();
            addSkill();
        });
    }

    // Match score filter listener
    if (matchScoreFilter) {
        matchScoreFilter.addEventListener('input', function(e) {
            DOM.byId('matchScoreValue').textContent = e.target.value;
        });
    }

    // Max recommendations slider listener
    if (maxRecommendationsSlider) {
        maxRecommendationsSlider.addEventListener('input', function(e) {
            DOM.byId('maxRecommendationsValue').textContent = e.target.value;
        });
    }

    // Fetch jobs button
    if (fetchJobsBtn) {
        fetchJobsBtn.addEventListener('click', async function(e) {
            e.preventDefault();
            await handleFetchJobs();
        });
    }

    // Form submission
    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            await handleGetRecommendations();
        });
    }

    // Clear button listener
    const clearFormBtn = DOM.byId('clearFormBtn');
    if (clearFormBtn) {
        clearFormBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clearAllFields();
        });
    }
}

// Add Skill
function addSkill() {
    const skillInput = DOM.byId('skillInput');
    const skill = skillInput.value.trim();

    if (!skill) {
        Alert.warning('Please enter a skill');
        return;
    }

    if (userSkills.includes(skill)) {
        Alert.warning('Skill already added');
        skillInput.value = '';
        return;
    }

    userSkills.push(skill);
    skillInput.value = '';

    // Save profile
    saveProfile();

    // Update display
    renderSkillsTags();
}

// Remove Skill
function removeSkill(skill) {
    userSkills = ArrayUtils.remove(userSkills, skill);
    
    // Save profile
    saveProfile();
    
    // Update display
    renderSkillsTags();
}

// Render Skills Tags
function renderSkillsTags() {
    const skillsTags = DOM.byId('skillsTags');
    skillsTags.innerHTML = '';

    userSkills.forEach(skill => {
        const tag = DOM.create('div', {
            className: 'tag tag-removable',
            innerHTML: `<span>${skill}</span><i class="fas fa-times" style="cursor: pointer;"></i>`,
            onClick: () => removeSkill(skill),
        });
        skillsTags.appendChild(tag);
    });
}

// Clear All Form Fields
function clearAllFields() {
    // Clear skills
    userSkills = [];
    DOM.byId('skillInput').value = '';
    renderSkillsTags();

    // Reset all select dropdowns
    const roleSelect = DOM.byId('roleSelect');
    if (roleSelect) roleSelect.value = '';

    const experienceSelect = DOM.byId('experienceSelect');
    if (experienceSelect) experienceSelect.value = '';

    const locationSelect = DOM.byId('locationSelect');
    if (locationSelect) locationSelect.value = '';

    // Reset all sliders and filters
    const matchScoreFilter = DOM.byId('matchScoreFilter');
    if (matchScoreFilter) {
        matchScoreFilter.value = '0';
        DOM.byId('matchScoreValue').textContent = '0';
    }

    const maxRecommendationsSlider = DOM.byId('maxRecommendationsSlider');
    if (maxRecommendationsSlider) {
        maxRecommendationsSlider.value = '10';
        DOM.byId('maxRecommendationsValue').textContent = '10';
    }

    // Reset checkboxes
    const locationMatchFilter = DOM.byId('locationMatchFilter');
    if (locationMatchFilter) locationMatchFilter.checked = false;

    const skillsMatchFilter = DOM.byId('skillsMatchFilter');
    if (skillsMatchFilter) skillsMatchFilter.checked = false;

    // Clear recommendations display
    const recommendationsDiv = DOM.byId('recommendationsDiv');
    if (recommendationsDiv) {
        recommendationsDiv.innerHTML = '';
    }

    // Clear saved profile from localStorage
    localStorage.removeItem('userProfile');

    // Show success message
    Alert.success('All fields cleared');
}

// Handle Get Recommendations
// Handle Fetch Jobs - Refresh database and train model
async function handleFetchJobs() {
    const fetchJobsBtn = DOM.byId('fetchJobsBtn');
    
    if (!confirm('🔄 This will fetch latest jobs from the API, delete old data, and retrain the recommendation model. This may take 1-2 minutes.\n\nContinue?')) {
        return;
    }

    try {
        // Disable button and show loading
        fetchJobsBtn.disabled = true;
        const originalHTML = fetchJobsBtn.innerHTML;
        fetchJobsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';

        // Call fetch-jobs endpoint
        const response = await fetch(`${API_BASE_URL}/api/fetch-jobs`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            console.log('✅ Fetch jobs successful:', result);
            Alert.success(`✅ Job database updated!\n\n${result.message}\n\nNew model trained and ready for recommendations.`, {
                duration: 5000
            });
            
            // Reload recommendations if any exist
            const recommendationsContainer = DOM.byId('recommendationsContainer');
            if (recommendationsContainer && recommendationsContainer.innerHTML.trim() !== '') {
                console.log('Reloading recommendations with new model...');
                await handleGetRecommendations();
            }
        } else {
            Alert.error(`Failed to fetch jobs:\n\n${result.message}`);
        }
    } catch (error) {
        console.error('Error fetching jobs:', error);
        Alert.error(`Error fetching jobs:\n\n${error.message}`);
    } finally {
        // Re-enable button
        const fetchJobsBtn = DOM.byId('fetchJobsBtn');
        fetchJobsBtn.disabled = false;
        fetchJobsBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Job Data';
    }
}

async function handleGetRecommendations() {
    const roleSelect = DOM.byId('roleSelect');
    const experienceSelect = DOM.byId('experienceSelect');
    const locationSelect = DOM.byId('locationSelect');
    const recommendationsContainer = DOM.byId('recommendationsContainer');
    const matchScoreFilter = DOM.byId('matchScoreFilter');
    const locationMatchFilter = DOM.byId('locationMatchFilter');
    const skillsMatchFilter = DOM.byId('skillsMatchFilter');
    const maxRecommendationsSlider = DOM.byId('maxRecommendationsSlider');

    // Validate
    if (!roleSelect.value) {
        Alert.warning('Please select a job role');
        return;
    }

    if (!experienceSelect.value) {
        Alert.warning('Please select experience level');
        return;
    }

    if (!locationSelect.value) {
        Alert.warning('Please select preferred location');
        return;
    }

    if (userSkills.length === 0) {
        Alert.warning('Please add at least one skill');
        return;
    }

    try {
        // Show loading
        recommendationsContainer.innerHTML = '<div class="spinner" style="margin: var(--spacing-2xl) 0;"></div>';

        // Get max recommendations value
        const maxRecommendations = parseInt(maxRecommendationsSlider.value) || 10;

        const userProfile = {
            role: roleSelect.value,
            experience: experienceSelect.value,
            location: locationSelect.value,
            skills: userSkills,
            preferred_locations: [locationSelect.value],
            top_n: maxRecommendations  // Pass max recommendations
        };

        // Save profile
        Storage.set(STORAGE_KEYS.USER_PROFILE, userProfile);

        // Get recommendations
        let recommendations = await API.getRecommendations(userProfile);

        // Apply filters if enabled
        if (recommendations && recommendations.length > 0) {
            // Filter by match score
            const minMatchScore = parseInt(matchScoreFilter.value) || 0;
            recommendations = recommendations.filter(job => (job.match_score || 0) >= minMatchScore);
            
            // Filter by location match only
            if (locationMatchFilter && locationMatchFilter.checked) {
                recommendations = recommendations.filter(job => {
                    const locationScore = job.location_match || 0;
                    return locationScore >= 80; // Only exact location matches
                });
            }
            
            // Filter by skills match only
            if (skillsMatchFilter && skillsMatchFilter.checked) {
                recommendations = recommendations.filter(job => {
                    const skillsScore = job.skills_match || 0;
                    return skillsScore >= 80; // Only strong skill matches
                });
            }
        }

        if (recommendations && recommendations.length > 0) {
            renderRecommendations(recommendations);
            Alert.success(`Loaded ${recommendations.length} recommendations!`);
        } else {
            recommendationsContainer.innerHTML = `
                <div class="card">
                    <div class="card-body" style="text-align: center;">
                        <p style="color: var(--text-secondary); margin: var(--spacing-xl) 0;">
                            No recommendations found. Try adjusting your filters.
                        </p>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error getting recommendations:', error);
        Alert.error('Failed to get recommendations: ' + error.message);
        recommendationsContainer.innerHTML = `
            <div class="alert alert-error">
                Error: ${error.message}
            </div>
        `;
    }
}

// Render Recommendations
function renderRecommendations(recommendations) {
    const container = DOM.byId('recommendationsContainer');
    container.innerHTML = '';

    // Update metrics
    updateRecommendationMetrics(recommendations);

    // Create grid for job cards - Full width stacked layout
    const jobsGrid = DOM.create('div', {
        style: 'display: grid; grid-template-columns: 1fr; gap: var(--spacing-lg);',
    });

    recommendations.forEach((job, index) => {
        // Calculate match score color
        const matchScore = job.match_score || 0;
        let matchColor = '#ef4444'; // red
        let matchBadgeBg = '#fee2e2';
        if (matchScore >= 60) {
            matchColor = '#22c55e'; // green
            matchBadgeBg = '#dcfce7';
        } else if (matchScore >= 40) {
            matchColor = '#f59e0b'; // amber
            matchBadgeBg = '#fef3c7';
        }

        // Determine fit category
        let fitCategory = 'Low Fit';
        let fitCategoryColor = '#ef4444';
        if (matchScore >= 70) {
            fitCategory = 'Best Fit';
            fitCategoryColor = '#10b981';
        } else if (matchScore >= 40) {
            fitCategory = 'Average Fit';
            fitCategoryColor = '#f59e0b';
        }

        const card = DOM.create('div', {
            className: 'card',
            style: 'display: flex; flex-direction: column; transition: transform 0.2s, box-shadow 0.2s;',
            onMouseEnter: (e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.1)';
            },
            onMouseLeave: (e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
            },
        });

        // Header with title and match badge
        const header = DOM.create('div', {
            style: 'position: relative; padding-bottom: var(--spacing-md); border-bottom: 1px solid var(--border-color);',
        });

        const titleSection = DOM.create('div');
        titleSection.innerHTML = `
            <h4 style="margin: 0 0 var(--spacing-xs) 0; font-size: 16px; line-height: 1.4;">
                <i class="fas fa-briefcase" style="color: var(--primary-color); margin-right: 6px;"></i>
                ${job.title || 'Job Title'}
            </h4>
        `;

        // Match Score Badge with fit category
        const matchBadge = DOM.create('div', {
            style: `position: absolute; top: 0; right: 0; background: ${matchBadgeBg}; color: ${matchColor}; 
                    padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 14px;`,
            innerHTML: `${Math.round(matchScore)}% Match · <span style="color: ${fitCategoryColor}; font-weight: 600;">${fitCategory}</span>`,
        });

        header.appendChild(titleSection);
        header.appendChild(matchBadge);

        const companySection = DOM.create('div', {
            style: 'margin-top: var(--spacing-sm); display: flex; align-items: center; gap: 6px;',
            innerHTML: `<i class="fas fa-building" style="color: var(--text-secondary);"></i>
                        <span style="color: var(--text-secondary);">${job.company || 'Company'}</span>`,
        });
        header.appendChild(companySection);

        // Location and time
        const metaRow = DOM.create('div', {
            style: 'display: flex; gap: var(--spacing-lg); margin: var(--spacing-md) 0; font-size: 13px; color: var(--text-secondary);',
        });

        const locationMeta = DOM.create('div', {
            innerHTML: `<i class="fas fa-map-marker-alt" style="color: #ef4444; margin-right: 4px;"></i>
                       ${job.location || 'Not specified'}`,
        });

        const timeMeta = DOM.create('div', {
            innerHTML: `<i class="fas fa-clock" style="color: #3b82f6; margin-right: 4px;"></i>
                       ${job.posted_date ? '21 days ago' : 'Recently posted'}`,
        });

        metaRow.appendChild(locationMeta);
        metaRow.appendChild(timeMeta);

        header.appendChild(metaRow);

        // Body - description and skills
        const body = DOM.create('div', { style: 'flex: 1; padding: var(--spacing-lg) 0; padding-bottom: var(--spacing-md);' });

        // Description section - Initially hidden, with toggle button
        let descSection = null;
        if (job.description) {
            descSection = DOM.create('div', {
                style: 'margin-bottom: var(--spacing-lg); padding: var(--spacing-md); background: #f8f9fa; border-radius: var(--border-radius-md); display: none;'
            });
            
            const descTitle = DOM.create('p', {
                style: 'margin: 0 0 var(--spacing-sm) 0; font-size: 12px; color: var(--text-secondary); font-weight: 600;',
            }, 'About');
            descSection.appendChild(descTitle);
            
            const desc = DOM.create('p', {
                style: 'color: var(--text-secondary); font-size: 13px; line-height: 1.5; margin: 0;',
            }, job.description);
            descSection.appendChild(desc);
            
            body.appendChild(descSection);
        }

        // Skills section with matching logic
        if (job.required_skills && job.required_skills.length > 0) {
            const skillsSection = DOM.create('div', { 
                style: 'margin-bottom: var(--spacing-md);' 
            });
            
            // Your Skills (matching)
            const userSkillsLower = userSkills.map(s => s.toLowerCase());
            const matchedSkills = job.required_skills.filter(skill => 
                userSkillsLower.includes(skill.toLowerCase())
            );
            const missingSkills = job.required_skills.filter(skill => 
                !userSkillsLower.includes(skill.toLowerCase())
            );

            // "Why the match is low/average" section
            if (matchScore < 70 && missingSkills.length > 0) {
                const whyLowTitle = DOM.create('p', {
                    style: `font-size: 13px; color: var(--text-primary); margin: 0 0 var(--spacing-sm) 0; font-weight: 600; 
                           display: flex; align-items: center; gap: 6px;`,
                    innerHTML: `<i class="fas fa-exclamation-triangle" style="color: ${fitCategoryColor};"></i> Why the match is ${fitCategory.toLowerCase().split(' ')[0]}`,
                });
                skillsSection.appendChild(whyLowTitle);

                const reasonsList = DOM.create('div', {
                    style: 'margin-bottom: var(--spacing-md); padding: var(--spacing-sm); background: #fef3c7; border-left: 3px solid #f59e0b; border-radius: 4px;'
                });

                // Show missing skills as reasons
                if (missingSkills.length > 0) {
                    const reasonItem = DOM.create('p', {
                        style: 'margin: 0 0 var(--spacing-xs) 0; font-size: 12px; color: var(--text-primary);',
                        innerHTML: `<i class="fas fa-times" style="color: #ef4444; margin-right: 6px;"></i>Missing: ${missingSkills.slice(0, 3).join(', ')}${missingSkills.length > 3 ? '...' : ''}`
                    });
                    reasonsList.appendChild(reasonItem);
                }

                skillsSection.appendChild(reasonsList);
            }

            // Your Strengths (matched skills)
            if (matchedSkills.length > 0) {
                const yourSkillsTitle = DOM.create('p', {
                    style: 'font-size: 12px; color: var(--text-primary); margin: 0 0 var(--spacing-sm) 0; font-weight: 600;',
                    innerHTML: '<i class="fas fa-check-circle" style="color: #10b981; margin-right: 6px;"></i>Your Strengths',
                });
                skillsSection.appendChild(yourSkillsTitle);

                const skillsTags = DOM.create('div', {
                    style: 'display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--spacing-md);',
                });

                matchedSkills.forEach(skill => {
                    const tag = DOM.create('span', {
                        style: `display: inline-block; background: #e0e7ff; color: var(--primary-color); 
                                padding: 6px 12px; border-radius: 14px; font-size: 13px; font-weight: 500;`,
                        innerHTML: `${skill}`,
                    });
                    skillsTags.appendChild(tag);
                });

                skillsSection.appendChild(skillsTags);
            }

            // Missing Skills to Learn
            if (missingSkills.length > 0) {
                const missingTitle = DOM.create('p', {
                    style: 'font-size: 12px; color: var(--text-primary); margin: var(--spacing-md) 0 var(--spacing-sm) 0; font-weight: 600;',
                    innerHTML: '<i class="fas fa-graduation-cap" style="color: #f59e0b; margin-right: 6px;"></i>Skills to Learn',
                });
                skillsSection.appendChild(missingTitle);

                const missingTags = DOM.create('div', {
                    style: 'display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: var(--spacing-md);',
                });

                missingSkills.forEach(skill => {
                    const tag = DOM.create('span', {
                        style: `display: inline-block; background: #fef3c7; color: #92400e; 
                                padding: 6px 12px; border-radius: 14px; font-size: 13px; font-weight: 500;`,
                        innerHTML: `${skill}`,
                    });
                    missingTags.appendChild(tag);
                });

                skillsSection.appendChild(missingTags);
            }

            body.appendChild(skillsSection);
        }

        // Footer - Salary and actions
        const footer = DOM.create('div', {
            style: 'padding-top: var(--spacing-lg); border-top: 1px solid var(--border-color);',
        });

        const salarySection = DOM.create('div', {
            style: 'margin-bottom: var(--spacing-lg); display: flex; align-items: center; gap: 6px; font-weight: 600;',
        });
        const salary = job.salary_max ? Format.currency(job.salary_max) : 'Salary not specified';
        salarySection.innerHTML = `<i class="fas fa-indian-rupee-sign" style="color: #10b981;"></i>${salary}`;
        footer.appendChild(salarySection);

        // Action buttons - All in one row
        const buttonGroup = DOM.create('div', {
            style: 'display: grid; grid-template-columns: 1fr 1fr 1fr; gap: var(--spacing-md);',
        });

        // View Details button for About section
        if (descSection) {
            const viewDetailsBtn = DOM.create('button', {
                className: 'btn btn-secondary',
                style: 'padding: 8px 12px; font-size: 13px;',
                innerHTML: '<i class="fas fa-eye"></i> View Details',
                onClick: () => {
                    if (descSection.style.display === 'none') {
                        descSection.style.display = 'block';
                        viewDetailsBtn.innerHTML = '<i class="fas fa-eye-slash"></i> Hide Details';
                    } else {
                        descSection.style.display = 'none';
                        viewDetailsBtn.innerHTML = '<i class="fas fa-eye"></i> View Details';
                    }
                },
            });
            buttonGroup.appendChild(viewDetailsBtn);
        }

        const saveBtn = DOM.create('button', {
            className: 'btn btn-secondary',
            style: 'padding: 8px 12px; font-size: 13px;',
            innerHTML: '<i class="fas fa-bookmark"></i> Save',
            onClick: () => saveJob(job),
        });

        const applyBtn = DOM.create('a', {
            className: 'btn btn-primary',
            href: job.url || '#',
            target: '_blank',
            style: 'padding: 8px 12px; font-size: 13px; text-align: center;',
            innerHTML: '<i class="fas fa-arrow-right"></i> Apply Now',
        });

        buttonGroup.appendChild(saveBtn);
        buttonGroup.appendChild(applyBtn);
        footer.appendChild(buttonGroup);

        card.appendChild(header);
        card.appendChild(body);
        card.appendChild(footer);

        jobsGrid.appendChild(card);
    });

    container.appendChild(jobsGrid);

    // Add Skills Development Path section
    if (recommendations.length > 0) {
        addSkillsDevelopmentPath(recommendations, container);
    }
}

// Add Skills Development Path Section
function addSkillsDevelopmentPath(recommendations, container) {
    // Collect all missing skills and count frequency
    const skillFrequency = {};
    const userSkillsLower = userSkills.map(s => s.toLowerCase());

    recommendations.forEach(job => {
        if (job.required_skills && Array.isArray(job.required_skills)) {
            job.required_skills.forEach(skill => {
                const skillLower = skill.toLowerCase();
                // Only count if user doesn't already have it
                if (!userSkillsLower.includes(skillLower)) {
                    skillFrequency[skill] = (skillFrequency[skill] || 0) + 1;
                }
            });
        }
    });

    // Get top 5 most in-demand missing skills
    const topSkills = Object.entries(skillFrequency)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .map(([skill, count]) => ({ skill, count }));

    if (topSkills.length === 0) return;

    // Create section
    const skillsSection = DOM.create('div', {
        style: 'margin-top: var(--spacing-3xl); padding: var(--spacing-2xl); background: linear-gradient(135deg, #f0f4ff, #f8f5ff); border-radius: var(--border-radius-lg);'
    });

    const title = DOM.create('h3', {
        style: 'margin: 0 0 var(--spacing-sm) 0; color: var(--primary-color); font-size: 20px;',
        innerHTML: '🚀 Skills Development Path'
    });
    skillsSection.appendChild(title);

    const subtitle = DOM.create('p', {
        style: 'margin: 0 0 var(--spacing-lg) 0; color: var(--text-secondary); font-size: 14px;',
        innerHTML: 'Focus on these in-demand skills to increase your match scores:'
    });
    skillsSection.appendChild(subtitle);

    // Skills grid
    const skillsGrid = DOM.create('div', {
        style: 'display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: var(--spacing-md);'
    });

    // Skill icons mapping
    const skillIcons = {
        'Python': '🐍',
        'Java': '☕',
        'JavaScript': '📜',
        'SQL': '🗄️',
        'AI': '💡',
        'Machine Learning': '🤖',
        'AWS': '☁️',
        'Docker': '🐳',
        'Kubernetes': '⚙️',
        'React': '⚛️',
        'Node.js': '📦',
        'Go': '🐹',
        'Rust': '🦀',
        'TypeScript': '📘',
        'C++': '➕',
        'Git': '🌿',
        'Linux': '🐧'
    };

    topSkills.forEach(({ skill, count }) => {
        const skillCard = DOM.create('div', {
            style: `padding: var(--spacing-md); background: white; border-radius: 8px; border-left: 4px solid var(--primary-color); 
                   text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08);`
        });

        const icon = DOM.create('div', {
            style: 'font-size: 28px; margin-bottom: 8px;',
            innerHTML: skillIcons[skill] || '💼'
        });
        skillCard.appendChild(icon);

        const skillName = DOM.create('p', {
            style: 'margin: 0 0 6px 0; font-weight: 600; color: var(--text-primary); font-size: 13px;',
            innerHTML: skill
        });
        skillCard.appendChild(skillName);

        const count_text = DOM.create('p', {
            style: 'margin: 0; font-size: 12px; color: var(--text-secondary);',
            innerHTML: `Required by ${count} ${count === 1 ? 'job' : 'jobs'}`
        });
        skillCard.appendChild(count_text);

        skillsGrid.appendChild(skillCard);
    });

    skillsSection.appendChild(skillsGrid);
    container.appendChild(skillsSection);
}

// Update Recommendation Metrics
function updateRecommendationMetrics(recommendations) {
    if (recommendations.length === 0) return;

    const totalMatches = recommendations.length;
    const avgMatch = Math.round(
        recommendations.reduce((sum, job) => sum + (job.match_score || 0), 0) / totalMatches
    );

    const companies = new Set(recommendations.map(j => j.company)).size;
    const locations = new Set(recommendations.map(j => j.location)).size;

    DOM.byId('totalMatchesMetric').textContent = totalMatches;
    DOM.byId('avgMatchMetric').textContent = avgMatch + '%';
    DOM.byId('companiesMetric').textContent = companies;
    DOM.byId('locationsMetric').textContent = locations;
}

// Save Job
function saveJob(job) {
    let savedJobs = Storage.get(STORAGE_KEYS.SAVED_JOBS, []);

    // Check if already saved
    if (savedJobs.some(j => j.id === job.id)) {
        Alert.warning('Job already saved');
        return;
    }

    savedJobs.push(job);
    Storage.set(STORAGE_KEYS.SAVED_JOBS, savedJobs);

    Alert.success('Job saved! View it in Saved Jobs.');
}

// Load Saved Profile
function loadSavedProfile() {
    const profile = Storage.get(STORAGE_KEYS.USER_PROFILE);

    if (profile) {
        const roleSelect = DOM.byId('roleSelect');
        const experienceSelect = DOM.byId('experienceSelect');
        const locationSelect = DOM.byId('locationSelect');

        if (profile.role) roleSelect.value = profile.role;
        if (profile.experience) experienceSelect.value = profile.experience;
        if (profile.location) locationSelect.value = profile.location;
        if (profile.skills) {
            userSkills = profile.skills;
            renderSkillsTags();
        }
    }
}

// Save Profile
function saveProfile() {
    const roleSelect = DOM.byId('roleSelect');
    const experienceSelect = DOM.byId('experienceSelect');
    const locationSelect = DOM.byId('locationSelect');

    const profile = {
        role: roleSelect.value,
        experience: experienceSelect.value,
        location: locationSelect.value,
        skills: userSkills,
        preferred_locations: [locationSelect.value],
    };

    Storage.set(STORAGE_KEYS.USER_PROFILE, profile);
}
