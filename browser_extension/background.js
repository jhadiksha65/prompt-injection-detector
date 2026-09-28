/**
 * background.js
 * Chrome Extension Service Worker acting as the bridge between browser DOM
 * scripts and the Flask Security API's real end-to-end dual-layer pipeline
 * (POST /secure-prompt — the same endpoint and verdict contract the web UI
 * uses). This file contains NO independent security decision logic: every
 * verdict (Layer 1 decision, Layer 2 decision, final_decision) comes
 * straight from the backend response and is passed through unmodified.
 */

importScripts("config.js");

// Handle messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

    // 1. Analyze a specific prompt string against the real backend pipeline.
    if (message.type === "CHECK_PROMPT") {
        const promptText = message.prompt || "";

        getApiBaseUrl().then((apiBaseUrl) => {
            fetch(`${apiBaseUrl}/secure-prompt`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                // Only the prompt is ever sent. No demo/debug flags — the
                // extension must never be able to trigger the Layer 2 demo
                // mechanism.
                body: JSON.stringify({ prompt: promptText })
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    return response.json();
                })
                .then((data) => {
                    recordLastScan(promptText, data);
                    sendResponse({ success: true, data });
                })
                .catch((error) => {
                    console.error("[PromptSecurity] Backend connection failed:", error);
                    sendResponse(_backendUnavailableResponse());
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

                getApiBaseUrl().then((apiBaseUrl) => {
                    // Forward captured text through the same real dual-layer
                    // pipeline used everywhere else (/secure-prompt).
                    fetch(`${apiBaseUrl}/secure-prompt`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ prompt: capturedText })
                    })
                        .then((res) => {
                            if (!res.ok) {
                                throw new Error(`HTTP error! status: ${res.status}`);
                            }
                            return res.json();
                        })
                        .then((data) => {
                            recordLastScan(capturedText, data);
                            sendResponse({ success: true, text: capturedText, data });
                        })
                        .catch((err) => {
                            sendResponse({
                                success: false,
                                text: capturedText,
                                error: "Security backend unreachable. Scan could not be confirmed."
                            });
                        });
                });
            });
        });

        return true;
    }

    // 3. Fetch latest scan summary from storage
    if (message.type === "GET_LAST_SCAN") {
        chrome.storage.local.get(["last_scan"], (result) => {
            sendResponse({ last_scan: result.last_scan || null });
        });
        return true;
    }

    // 4. Send an unlock/reauth request to the Flask server
    if (message.type === "UNLOCK_SESSION") {
        const password = message.password || "";
        getApiBaseUrl().then((apiBaseUrl) => {
            fetch(`${apiBaseUrl}/api/unlock`, {
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
                    sendResponse({ success: false, error: "Security backend unreachable." });
                });
        });
        return true;
    }
});

/**
 * A real backend failure (network error, non-2xx, unreachable host) must
 * fail CLOSED: the caller must never receive a synthesized "safe" verdict
 * that would let a prompt through when protection could not be confirmed.
 */
function _backendUnavailableResponse() {
    return {
        success: false,
        error: "Security backend unreachable. Protection could not be confirmed, so the prompt was not approved."
    };
}

/**
 * Records only a minimal, size-bounded scan SUMMARY for the popup to show
 * on reopen — never the full prompt text. Prompts are not something this
 * extension needs to retain; only the verdict is useful for the popup UI.
 */
function recordLastScan(promptText, backendResult) {
    const MAX_SNIPPET_CHARS = 100;
    const snippet = (promptText || "").slice(0, MAX_SNIPPET_CHARS);

    const scanRecord = {
        timestamp: new Date().toISOString(),
        prompt_snippet: snippet,
        prompt_truncated: (promptText || "").length > MAX_SNIPPET_CHARS,
        result: backendResult
    };
    chrome.storage.local.set({ last_scan: scanRecord });
}

console.log("[Prompt Injection Detector] Background service worker initialized.");
