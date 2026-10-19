/**
 * theme.js — Central Light/Dark Theme Controller
 * Synchronizes theme across Analyzer, External Demo, Dashboard, and Sensitive Resource.
 */
(function() {
    const THEME_KEY = 'prompt_security_theme';

    // 1. Immediately apply theme from storage to avoid flash of wrong theme
    function getStoredTheme() {
        try {
            return localStorage.getItem(THEME_KEY) || 'light';
        } catch (e) {
            return 'light';
        }
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
    }

    // Apply immediately during script parse
    applyTheme(getStoredTheme());

    function updateToggleIcon(btn, theme) {
        if (!btn) return;
        if (theme === 'dark') {
            btn.innerHTML = `
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="5"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>`;
            btn.setAttribute('title', 'Switch to Light Theme');
            btn.setAttribute('aria-label', 'Switch to Light Theme');
        } else {
            btn.innerHTML = `
                <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>`;
            btn.setAttribute('title', 'Switch to Dark Theme');
            btn.setAttribute('aria-label', 'Switch to Dark Theme');
        }
    }

    // 2. Setup toggle listener once DOM is ready
    function initToggle() {
        const toggleBtn = document.getElementById('themeToggleBtn');
        const current = getStoredTheme();
        applyTheme(current);
        updateToggleIcon(toggleBtn, current);

        if (toggleBtn && !toggleBtn._themeInitialized) {
            toggleBtn._themeInitialized = true;
            toggleBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const now = document.documentElement.getAttribute('data-theme') || 'light';
                const next = now === 'dark' ? 'light' : 'dark';
                try {
                    localStorage.setItem(THEME_KEY, next);
                } catch (e) {}
                applyTheme(next);
                updateToggleIcon(toggleBtn, next);
                window.dispatchEvent(new CustomEvent('themechanged', { detail: { theme: next } }));
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initToggle);
    } else {
        initToggle();
    }

    // Expose helpers globally if needed
    window.PromptSecurityTheme = {
        getTheme: getStoredTheme,
        setTheme: function(theme) {
            try { localStorage.setItem(THEME_KEY, theme); } catch (e) {}
            applyTheme(theme);
            const btn = document.getElementById('themeToggleBtn');
            updateToggleIcon(btn, theme);
            window.dispatchEvent(new CustomEvent('themechanged', { detail: { theme: theme } }));
        }
    };
})();
