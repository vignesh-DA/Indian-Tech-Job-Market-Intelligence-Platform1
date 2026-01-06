/* Configuration */

// API Configuration
const API_BASE_URL = 'http://localhost:5000';

const API_ENDPOINTS = {
    STATS: `${API_BASE_URL}/api/stats`,
    JOBS: `${API_BASE_URL}/api/jobs`,
    RECOMMENDATIONS: `${API_BASE_URL}/api/recommendations`,
    ANALYTICS: `${API_BASE_URL}/api/analytics`,
    FETCH_JOBS: `${API_BASE_URL}/api/fetch-jobs`,
    LAST_UPDATED: `${API_BASE_URL}/api/last-updated`,
    ROLES: `${API_BASE_URL}/api/roles`,
};

// Local Storage Keys
const STORAGE_KEYS = {
    USER_PROFILE: 'userProfile',
    SAVED_JOBS: 'savedJobs',
    APPLICATIONS: 'applications',
    THEME: 'theme',
};

// App Configuration
const APP_CONFIG = {
    JOBS_PER_PAGE: 20,
    DEBUG: false,
};

// Role Options - Will be loaded dynamically from API
let ROLES = [];

// Experience Options
const EXPERIENCE_LEVELS = [
    '0-2 years',
    '2-5 years',
    '5-10 years',
    '10+ years',
];

// Popular Skills
const POPULAR_SKILLS = [
    'JavaScript',
    'Python',
    'React',
    'Node.js',
    'Java',
    'SQL',
    'AWS',
    'Docker',
    'Kubernetes',
    'Git',
    'TypeScript',
    'Vue.js',
    'Angular',
    'MongoDB',
    'PostgreSQL',
    'REST APIs',
    'GraphQL',
    'Linux',
    'Microservices',
    'CI/CD',
];

// Indian Tech Hubs (normalized based on actual CSV data)
const LOCATIONS = [
    'Bangalore',
    'Chennai',
    'Delhi',
    'Hyderabad',
    'Mumbai',
    'Pune',
    'Remote',
];

// Initialize App
document.addEventListener('DOMContentLoaded', function() {
    console.log('App initializing...');
});
