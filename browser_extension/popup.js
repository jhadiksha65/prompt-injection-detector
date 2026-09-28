/**
 * popup.js
 * Controls the extension popup UI, handles on-demand scans, and
 * synchronizes with background service worker and local storage.
 *
 * Uses the same verdict contract as the web UI and the content script:
 * the backend's /secure-prompt response, with the Layer 1 verdict nested
 * under `layer1`, Layer 2 under `layer2`, and the combined outcome in
 * `final_decision`.
 */

document.addEventListener("DOMContentLoaded", () => {
    const scanBtn = document.getElementById("scanBtn");
    const retryBtn = document.getElementById("retryBtn");

    // Header
    const headerStatusDot = document.getElementById("headerStatusDot");
    const headerStatusText = document.getElementById("headerStatusText");

    // States
    const emptyState = document.getElementById("emptyState");
    const resultState = document.getElementById("resultState");

    // Result elements
    const resultHeader = document.getElementById("resultHeader");
    const topDecisionText = document.getElementById("topDecisionText");
    const riskScoreVal = document.getElementById("riskScoreVal");
    const progressBar = document.getElementById("progressBar");
    const reasonText = document.getElementById("reasonText");
    const attackType = document.getElementById("attackType");
    const decisionVal = document.getElementById("decisionVal");

    // Prompt
    const scannedPromptText = document.getElementById("scannedPromptText");
    const viewFullPrompt = document.getElementById("viewFullPrompt");

    // Settings
    const settingsToggle = document.getElementById("settingsToggle");
    const settingsPanel = document.getElementById("settingsPanel");
    const apiUrlInput = document.getElementById("apiUrlInput");
    const apiUrlSaveBtn = document.getElementById("apiUrlSaveBtn");
    const apiUrlStatus = document.getElementById("apiUrlStatus");

    let currentPromptFull = "";
    let currentPromptIsFull = false;

    function setEmptyStateMessage(title, message) {
        emptyState.textContent = "";
        const h4 = document.createElement("h4");
        h4.textContent = title;
        const p = document.createElement("p");
        p.textContent = message; // never innerHTML: message may echo backend text
        emptyState.appendChild(h4);
        emptyState.appendChild(p);
    }

    // 1. Check Backend Connectivity (configurable host, not hardcoded)
    function checkConnection() {
        getApiBaseUrl().then((apiBaseUrl) => {
            fetch(`${apiBaseUrl}/health`)
                .then((res) => {
                    if (res.ok) {
                        headerStatusText.textContent = "Connected";
                        headerStatusDot.className = "status-dot online";
                        scanBtn.style.display = "block";
                        retryBtn.style.display = "none";
                    } else {
                        throw new Error("Status " + res.status);
                    }
                })
                .catch(() => {
                    headerStatusText.textContent = "Backend Offline";
                    headerStatusDot.className = "status-dot offline";
                    scanBtn.style.display = "none";
                    retryBtn.style.display = "block";
                });
        });
    }

    checkConnection();

    retryBtn.addEventListener("click", () => {
        headerStatusText.textContent = "Connecting...";
        headerStatusDot.className = "status-dot";
        checkConnection();
    });

    // 2. Render scan record into UI, reading the /secure-prompt verdict
    //    contract (layer1 / layer2 / final_decision), same as the web UI.
    function renderScanResult(prompt, backendResult, isFullPrompt) {
        if (!backendResult) return;

        emptyState.style.display = "none";
        resultState.style.display = "block";

        const layer1 = backendResult.layer1 || backendResult;
        const overallDecision = backendResult.final_decision || layer1.decision || "UNKNOWN";

        const score = layer1.risk_score !== undefined ? layer1.risk_score : 0;
        const attack = layer1.attack_type || "Benign";
        const reason = layer1.reason || "Analysis complete.";

        // Update score & progress
        riskScoreVal.textContent = `${score}%`;
        progressBar.style.width = `${Math.min(100, Math.max(0, score))}%`;

        // Reset classes
        resultHeader.className = "result-header";
        progressBar.className = "risk-meter-fill";
        decisionVal.className = "info-value";

        // Update state styling based on the combined pipeline decision.
        if (overallDecision === "BLOCK") {
            topDecisionText.textContent = "THREAT DETECTED";
            resultHeader.classList.add("block");
            progressBar.classList.add("block");
            decisionVal.classList.add("decision-block");
        } else if (["WARNING", "MASK", "ERROR"].includes(overallDecision)) {
            topDecisionText.textContent = "PROMPT WARNING";
            resultHeader.classList.add("warn");
            progressBar.classList.add("warn");
            decisionVal.classList.add("decision-warn");
        } else {
            topDecisionText.textContent = "PROMPT SAFE";
            resultHeader.classList.add("safe");
            progressBar.classList.add("safe");
            decisionVal.classList.add("decision-allow");
        }

        // All dynamic text is set via textContent only — never innerHTML —
        // since these values ultimately derive from user-supplied prompt
        // content processed by the backend.
        attackType.textContent = attack;
        decisionVal.textContent = overallDecision;
        reasonText.textContent = reason;

        if (prompt) {
            currentPromptFull = prompt;
            currentPromptIsFull = !!isFullPrompt;
            if (isFullPrompt && prompt.length > 100) {
                scannedPromptText.textContent = prompt.substring(0, 100) + "...";
                viewFullPrompt.style.display = "block";
                viewFullPrompt.textContent = "View full prompt";
            } else {
                // Either short enough to show in full, or this is only a
                // stored snippet (nothing more to reveal) — no toggle needed.
                scannedPromptText.textContent = prompt;
                viewFullPrompt.style.display = "none";
            }
        }
    }

    viewFullPrompt.addEventListener("click", (e) => {
        e.preventDefault();
        if (!currentPromptIsFull) return;
        if (viewFullPrompt.textContent === "View full prompt") {
            scannedPromptText.textContent = currentPromptFull;
            viewFullPrompt.textContent = "Show less";
        } else {
            scannedPromptText.textContent = currentPromptFull.substring(0, 100) + "...";
            viewFullPrompt.textContent = "View full prompt";
        }
    });

    // 3. Load previous scan summary if available. Only a truncated snippet
    //    is ever persisted (see background.js recordLastScan) — never the
    //    full prompt — so there is nothing further to reveal here.
    chrome.runtime.sendMessage({ type: "GET_LAST_SCAN" }, (response) => {
        if (response && response.last_scan) {
            const last = response.last_scan;
            renderScanResult(last.prompt_snippet, last.result, false);
        }
    });

    // 4. Handle "Scan Current Prompt" button
    scanBtn.addEventListener("click", () => {
        scanBtn.disabled = true;
        scanBtn.textContent = "Analyzing...";

        chrome.runtime.sendMessage({ type: "SCAN_CURRENT_TAB" }, (response) => {
            scanBtn.disabled = false;
            scanBtn.textContent = "Scan Current Prompt";

            if (!response || !response.success) {
                emptyState.style.display = "block";
                resultState.style.display = "none";
                setEmptyStateMessage(
                    "Error",
                    response?.error || "No text found in input box or backend offline."
                );
                return;
            }

            // response.text is only ever held in memory for this popup
            // session (never persisted) — see background.js.
            renderScanResult(response.text, response.data, true);
        });
    });

    // 5. Settings: configurable backend API host (never hardcoded-only).
    if (settingsToggle && settingsPanel) {
        settingsToggle.addEventListener("click", () => {
            const isOpen = settingsPanel.style.display === "block";
            settingsPanel.style.display = isOpen ? "none" : "block";
            if (!isOpen) {
                getApiBaseUrl().then((url) => {
                    apiUrlInput.value = url;
                });
            }
        });
    }

    if (apiUrlSaveBtn) {
        apiUrlSaveBtn.addEventListener("click", () => {
            const newUrl = apiUrlInput.value.trim();
            apiUrlStatus.textContent = "";

            setApiBaseUrl(newUrl).then((success) => {
                if (!success) {
                    apiUrlStatus.textContent = "Invalid URL. Use http(s)://host:port.";
                    apiUrlStatus.style.color = "#ef4444";
                    return;
                }

                // Manifest V3: an arbitrary configured production host needs
                // its host permission granted at runtime (optional_host_permissions
                // in manifest.json) before the service worker can fetch it.
                try {
                    const origin = new URL(newUrl).origin + "/*";
                    chrome.permissions.request({ origins: [origin] }, (granted) => {
                        apiUrlStatus.style.color = granted ? "#10b981" : "#f59e0b";
                        apiUrlStatus.textContent = granted
                            ? "Saved. Backend host updated."
                            : "Saved, but permission for this host was not granted — requests may fail.";
                        checkConnection();
                    });
                } catch (err) {
                    apiUrlStatus.textContent = "Saved.";
                    apiUrlStatus.style.color = "#10b981";
                    checkConnection();
                }
            });
        });
    }
});
