/* API Helper Functions */

class APIClient {
    constructor(baseURL = API_BASE_URL) {
        this.baseURL = baseURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
        };

        try {
            if (APP_CONFIG.DEBUG) {
                console.log(`${options.method || 'GET'} ${url}`, options);
            }

            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (APP_CONFIG.DEBUG) {
                console.log('Response:', data);
            }

            return data;
        } catch (error) {
            console.error(`API Error: ${error.message}`);
            throw error;
        }
    }

    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    // POST request
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // PUT request
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }
}

// Create global API client instance
const api = new APIClient(API_BASE_URL);

// API Methods
const API = {
    // Get statistics
    async getStats() {
        try {
            const response = await api.get('/api/stats');
            if (response.success) {
                return response.data;
            }
            throw new Error(response.message);
        } catch (error) {
            console.error('Error fetching stats:', error);
            return null;
        }
    },

    // Get jobs with filtering
    async getJobs(page = 1, limit = 20, filters = {}) {
        try {
            const params = {
                page,
                limit,
                ...filters,
            };
            const response = await api.get('/api/jobs', params);
            if (response.success) {
                return response.data;
            }
            throw new Error(response.message);
        } catch (error) {
            console.error('Error fetching jobs:', error);
            return null;
        }
    },

    // Get recommendations
    async getRecommendations(userProfile) {
        try {
            const response = await api.post('/api/recommendations', userProfile);
            if (response.success) {
                return response.data;
            }
            throw new Error(response.message);
        } catch (error) {
            console.error('Error fetching recommendations:', error);
            return null;
        }
    },

    // Get analytics
    async getAnalytics() {
        try {
            const response = await api.get('/api/analytics');
            if (response.success) {
                return response.data;
            }
            throw new Error(response.message);
        } catch (error) {
            console.error('Error fetching analytics:', error);
            return null;
        }
    },

    // Fetch latest jobs
    async fetchJobs() {
        try {
            const response = await api.post('/api/fetch-jobs');
            if (response.success) {
                return response;
            }
            throw new Error(response.message);
        } catch (error) {
            console.error('Error fetching jobs:', error);
            throw error;
        }
    },

    // Get last updated timestamp
    async getLastUpdated() {
        try {
            const response = await api.get('/api/last-updated');
            if (response.success) {
                return response.last_updated;
            }
            throw new Error(response.message);
        } catch (error) {
            console.error('Error fetching last updated:', error);
            return 'Unknown';
        }
    },
};

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { APIClient, API };
}
