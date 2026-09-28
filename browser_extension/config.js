/**
 * config.js
 * Shared, configurable backend API host for the extension. Loaded by both
 * background.js (service worker) and popup.js (classic script) so there is
 * a single source of truth for "where is the security backend" instead of
 * a hardcoded localhost-only URL baked into production behavior.
 */

// Only used the first time the extension runs, or if storage is unavailable.
// A deployer can still point production installs at a real host by setting
// this value via the popup Settings panel (persisted in chrome.storage.local).
const DEFAULT_API_BASE_URL = "http://localhost:5000";
const API_BASE_URL_STORAGE_KEY = "api_base_url";

/**
 * Resolves the configured backend API base URL (no trailing slash).
 * Always resolves (never rejects) — falls back to DEFAULT_API_BASE_URL if
 * storage is empty or unavailable.
 */
function getApiBaseUrl() {
    return new Promise((resolve) => {
        try {
            chrome.storage.local.get([API_BASE_URL_STORAGE_KEY], (result) => {
                const stored = result && result[API_BASE_URL_STORAGE_KEY];
                resolve(_normalizeBaseUrl(stored) || DEFAULT_API_BASE_URL);
            });
        } catch (err) {
            resolve(DEFAULT_API_BASE_URL);
        }
    });
}

/**
 * Persists a new backend API base URL. Returns a Promise<boolean> for success.
 */
function setApiBaseUrl(url) {
    const normalized = _normalizeBaseUrl(url);
    if (!normalized) {
        return Promise.resolve(false);
    }
    return new Promise((resolve) => {
        try {
            chrome.storage.local.set({ [API_BASE_URL_STORAGE_KEY]: normalized }, () => {
                resolve(true);
            });
        } catch (err) {
            resolve(false);
        }
    });
}

function _normalizeBaseUrl(url) {
    if (!url || typeof url !== "string") return null;
    const trimmed = url.trim().replace(/\/+$/, "");
    if (!/^https?:\/\/[^\s]+$/i.test(trimmed)) return null;
    return trimmed;
}
