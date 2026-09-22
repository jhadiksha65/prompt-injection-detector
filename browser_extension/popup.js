/**
 * popup.js
 * Controls the extension popup UI, handles on-demand scans,
 * and synchronizes with background service worker and local storage.
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

    let currentPromptFull = "";

    // 1. Check Backend Connectivity
    function checkConnection() {
        fetch("http://localhost:5000/health")
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
    }
    
    checkConnection();
    
    retryBtn.addEventListener("click", () => {
        headerStatusText.textContent = "Connecting...";
        headerStatusDot.className = "status-dot";
        checkConnection();
    });

    // 2. Render scan record into UI
    function renderScanResult(prompt, result) {
        if (!result) return;
        
        emptyState.style.display = "none";
        resultState.style.display = "block";

        const score = result.risk_score !== undefined ? result.risk_score : 0;
        const decision = result.decision || "ALLOW";
        const attack = result.attack_type || "Benign";
        const reason = result.reason || "Analysis complete.";

        // Update score & progress
        riskScoreVal.textContent = `${score}%`;
        progressBar.style.width = `${Math.min(100, Math.max(0, score))}%`;

        // Reset classes
        resultHeader.className = "result-header";
        progressBar.className = "risk-meter-fill";
        decisionVal.className = "info-value";

        // Update state styling based on decision/risk
        if (decision === "BLOCK" || score >= 80) {
            topDecisionText.textContent = "THREAT DETECTED";
            resultHeader.classList.add("block");
            progressBar.classList.add("block");
            decisionVal.classList.add("decision-block");
        } else if (decision === "WARN" || decision === "WARNING" || score > 30) {
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

        // Update labels
        attackType.textContent = attack;
        decisionVal.textContent = decision;
        reasonText.textContent = reason;

        if (prompt) {
            currentPromptFull = prompt;
            if (prompt.length > 100) {
                scannedPromptText.textContent = prompt.substring(0, 100) + "...";
                viewFullPrompt.style.display = "block";
                viewFullPrompt.textContent = "View full prompt";
            } else {
                scannedPromptText.textContent = prompt;
                viewFullPrompt.style.display = "none";
            }
        }
    }
    
    viewFullPrompt.addEventListener("click", (e) => {
        e.preventDefault();
        if (viewFullPrompt.textContent === "View full prompt") {
            scannedPromptText.textContent = currentPromptFull;
            viewFullPrompt.textContent = "Show less";
        } else {
            scannedPromptText.textContent = currentPromptFull.substring(0, 100) + "...";
            viewFullPrompt.textContent = "View full prompt";
        }
    });

    // 3. Load previous scan if available
    chrome.runtime.sendMessage({ type: "GET_LAST_SCAN" }, (response) => {
        if (response && response.last_scan) {
            const last = response.last_scan;
            renderScanResult(last.prompt, last.result);
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
                emptyState.innerHTML = `<h4>Error</h4><p>${response?.error || "No text found in input box or backend offline."}</p>`;
                return;
            }

            renderScanResult(response.text, response.data);
        });
    });
});