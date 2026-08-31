/**
 * background.js
 * Chrome Extension Service Worker acting as the bridge between browser DOM scripts
 * and the Flask Security API (http://localhost:5000/detect).
 */

const API_BASE_URL = "http://localhost:5000";

// Handle messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

    // 1. Analyze a specific prompt string against the Flask Security API
    if (message.type === "CHECK_PROMPT") {
        const promptText = message.prompt || "";

        fetch(`${API_BASE_URL}/detect`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ prompt: promptText })
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then((data) => {
            // Cache scan in local storage for popup inspection
            const scanRecord = {
                timestamp: new Date().toISOString(),
                prompt: promptText,
                result: data
            };
            chrome.storage.local.set({ last_scan: scanRecord });

            sendResponse({
                success: true,
                data: data
            });
        })
        .catch((error) => {
            console.error("[PromptSecurity] Backend connection failed:", error);
            // Fallback response if backend is offline
            sendResponse({
                success: false,
                error: "Backend API offline or unreachable (Ensure Flask server is running on port 5000)",
                data: {
                    is_injection: false,
                    decision: "ALLOW",
                    risk_score: 0,
                    risk_level: "LOW",
                    attack_type: "Benign",
                    reason: "Backend offline - heuristic bypass fallback."
                }
            });
        });

        return true; // Keep message channel open for asynchronous sendResponse
    }

    // 2. Query active tab for current prompt and trigger a live scan
    if (message.type === "SCAN_CURRENT_TAB") {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            const tabId = tabs[0]?.id;

            if (!tabId) {
                sendResponse({ success: false, error: "No active tab found." });
                return;
            }

            chrome.tabs.sendMessage(tabId, { type: "GET_CURRENT_PROMPT" }, (response) => {
                if (chrome.runtime.lastError || !response?.text) {
                    sendResponse({
                        success: false,
                        text: "",
                        error: "No prompt text found in active input box."
                    });
                    return;
                }

                const capturedText = response.text.trim();
                if (!capturedText) {
                    sendResponse({
                        success: false,
                        text: "",
                        error: "Input box is empty."
                    });
                    return;
                }

                // Forward captured text to /detect endpoint
                fetch(`${API_BASE_URL}/detect`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ prompt: capturedText })
                })
                .then((res) => res.json())
                .then((data) => {
                    const scanRecord = {
                        timestamp: new Date().toISOString(),
                        prompt: capturedText,
                        result: data
                    };
                    chrome.storage.local.set({ last_scan: scanRecord });

                    sendResponse({
                        success: true,
                        text: capturedText,
                        data: data
                    });
                })
                .catch((err) => {
                    sendResponse({
                        success: false,
                        text: capturedText,
                        error: "Flask backend unreachable."
                    });
                });
            });
        });

        return true;
    }

    // 3. Fetch latest scan from storage
    if (message.type === "GET_LAST_SCAN") {
        chrome.storage.local.get(["last_scan"], (result) => {
            sendResponse({ last_scan: result.last_scan || null });
        });
        return true;
    }

    // 4. Send an unlock/reauth request to the Flask server
    if (message.type === "UNLOCK_SESSION") {
        const password = message.password || "";
        fetch(`${API_BASE_URL}/api/unlock`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username: "admin", password: password })
        })
        .then((response) => response.json())
        .then((data) => {
            sendResponse({ success: data.success, data: data });
        })
        .catch((error) => {
            console.error("[PromptSecurity] Unlock request failed:", error);
            sendResponse({ success: false, error: "Flask backend unreachable." });
        });
        return true;
    }
});

console.log("[Prompt Injection Detector] Background service worker initialized.");