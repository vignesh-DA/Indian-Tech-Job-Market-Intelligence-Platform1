/* Utility Functions */

// DOM Utilities
const DOM = {
    // Get element by ID
    byId(id) {
        return document.getElementById(id);
    },

    // Get element by class
    byClass(className, parent = document) {
        return parent.querySelector(`.${className}`);
    },

    // Get all elements by class
    allByClass(className, parent = document) {
        return Array.from(parent.querySelectorAll(`.${className}`));
    },

    // Get element by selector
    select(selector, parent = document) {
        return parent.querySelector(selector);
    },

    // Get all elements by selector
    selectAll(selector, parent = document) {
        return Array.from(parent.querySelectorAll(selector));
    },

    // Create element
    create(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        for (const [key, value] of Object.entries(attributes)) {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key.startsWith('data-')) {
                element.setAttribute(key, value);
            } else if (key.startsWith('on')) {
                const eventName = key.slice(2).toLowerCase();
                element.addEventListener(eventName, value);
            } else {
                element.setAttribute(key, value);
            }
        }

        if (content) {
            element.textContent = content;
        }

        return element;
    },

    // Add class
    addClass(element, className) {
        element.classList.add(className);
    },

    // Remove class
    removeClass(element, className) {
        element.classList.remove(className);
    },

    // Toggle class
    toggleClass(element, className) {
        element.classList.toggle(className);
    },

    // Has class
    hasClass(element, className) {
        return element.classList.contains(className);
    },
};

// Local Storage Utilities
const Storage = {
    // Set item
    set(key, value) {
        try {
            localStorage.setItem(key, JSON.stringify(value));
        } catch (error) {
            console.error(`Error setting storage key ${key}:`, error);
        }
    },

    // Get item
    get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error(`Error getting storage key ${key}:`, error);
            return defaultValue;
        }
    },

    // Remove item
    remove(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.error(`Error removing storage key ${key}:`, error);
        }
    },

    // Clear all
    clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.error('Error clearing storage:', error);
        }
    },
};

// Format Utilities
const Format = {
    // Format number as currency
    currency(value, currency = '₹') {
        if (value >= 10000000) {
            return `${currency}${(value / 10000000).toFixed(1)}Cr`;
        }
        if (value >= 100000) {
            return `${currency}${(value / 100000).toFixed(1)}L`;
        }
        return `${currency}${value.toLocaleString('en-IN')}`;
    },

    // Format number with commas
    number(value) {
        return value.toLocaleString('en-IN');
    },

    // Format date
    date(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    },

    // Format date and time
    dateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    },

    // Format time ago
    timeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
        return this.date(dateString);
    },

    // Capitalize
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    },

    // Truncate string
    truncate(str, length = 100) {
        return str.length > length ? str.substring(0, length) + '...' : str;
    },
};

// Alert/Toast Utilities
const Alert = {
    // Show toast notification
    toast(message, type = 'info', duration = 3000) {
        const toast = DOM.create('div', {
            className: `toast ${type}`,
            innerHTML: message,
        });

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease-out forwards';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, duration);
    },

    // Success toast
    success(message, duration = 3000) {
        this.toast(`✅ ${message}`, 'success', duration);
    },

    // Error toast
    error(message, duration = 5000) {
        this.toast(`❌ ${message}`, 'error', duration);
    },

    // Info toast
    info(message, duration = 3000) {
        this.toast(`ℹ️ ${message}`, 'info', duration);
    },

    // Warning toast
    warning(message, duration = 4000) {
        this.toast(`⚠️ ${message}`, 'warning', duration);
    },
};

// Validation Utilities
const Validate = {
    // Email validation
    email(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // URL validation
    url(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },

    // Phone validation (Indian)
    phone(phone) {
        const re = /^[6-9]\d{9}$/;
        return re.test(phone.replace(/\D/g, ''));
    },

    // Not empty
    notEmpty(value) {
        return value && value.trim().length > 0;
    },

    // Min length
    minLength(value, length) {
        return value && value.length >= length;
    },

    // Max length
    maxLength(value, length) {
        return value && value.length <= length;
    },

    // Number
    number(value) {
        return !isNaN(value) && value !== '';
    },
};

// Array Utilities
const ArrayUtils = {
    // Remove item from array
    remove(array, item) {
        const index = array.indexOf(item);
        if (index > -1) {
            array.splice(index, 1);
        }
        return array;
    },

    // Remove duplicates
    unique(array) {
        return [...new Set(array)];
    },

    // Group by property
    groupBy(array, property) {
        return array.reduce((groups, item) => {
            const key = item[property];
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(item);
            return groups;
        }, {});
    },

    // Sort by property
    sortBy(array, property, ascending = true) {
        return [...array].sort((a, b) => {
            const aVal = a[property];
            const bVal = b[property];
            
            if (aVal < bVal) return ascending ? -1 : 1;
            if (aVal > bVal) return ascending ? 1 : -1;
            return 0;
        });
    },

    // Filter by property
    filterBy(array, property, value) {
        return array.filter(item => item[property] === value);
    },
};

// Debounce and Throttle
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => {
                inThrottle = false;
            }, limit);
        }
    };
}

// Promise utilities
const PromiseUtils = {
    // Wait/sleep
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    // Retry promise
    async retry(fn, retries = 3, delay = 1000) {
        for (let i = 0; i < retries; i++) {
            try {
                return await fn();
            } catch (error) {
                if (i === retries - 1) throw error;
                await this.wait(delay);
            }
        }
    },
};
