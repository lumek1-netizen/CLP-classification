// static/theme-toggle.js
/**
 * Dark Mode Toggle Script
 * Handles theme switching between light and dark modes
 */

// Get preferred theme from localStorage or system preference
const getPreferredTheme = () => {
    const stored = localStorage.getItem('theme');
    if (stored) {
        return stored;
    }

    // Check system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
};

// Apply theme to document
const setTheme = (theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    updateToggleIcon(theme);
};

// Update toggle button icon
const updateToggleIcon = (theme) => {
    const icon = document.querySelector('.theme-icon');
    if (icon) {
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }

    const btn = document.getElementById('theme-toggle-btn');
    if (btn) {
        btn.setAttribute('aria-label',
            theme === 'dark' ? 'Přepnout na světlý režim' : 'Přepnout na tmavý režim'
        );
    }
};

// Toggle between themes
const toggleTheme = () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
};

// Initialize theme on page load
document.addEventListener('DOMContentLoaded', () => {
    // Set initial theme
    const theme = getPreferredTheme();
    setTheme(theme);

    // Add click listener to toggle button
    const toggleBtn = document.getElementById('theme-toggle-btn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleTheme);
    }

    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Only auto-switch if user hasn't manually set a preference
        if (!localStorage.getItem('theme')) {
            setTheme(e.matches ? 'dark' : 'light');
        }
    });
});
