/**
 * popup.js
 * Controls the extension popup UI, handles on-demand scans,
 * and synchronizes with background service worker and local storage.
 */

document.addEventListener("DOMContentLoaded", () => {
    const scanBtn = document.getElementById("scanBtn");
    const statusBadge = document.getElementById("statusBadge");
    const riskScoreVal = document.getElementById("riskScoreVal");
    const progressBar = document.getElementById("progressBar");
    const attackType = document.getElementById("attackType");
    const decisionVal = document.getElementById("decisionVal");
    const reasonText = document.getElementById("reasonText");
    const scannedPromptText = document.getElementById("scannedPromptText");
    const scanTimestamp = document.getElementById("scanTimestamp");
    const backendStatus = document.getElementById("backendStatus");

    // 1. Check Backend Connectivity
    fetch("http://localhost:5000/health")
        .then((res) => {
            if (res.ok) {
                backendStatus.textContent = "● Backend Connected (Port 5000)";
                backendStatus.className = "backend-status online";
            } else {
                throw new Error("Status " + res.status);
            }
        })
        .catch(() => {
            backendStatus.textContent = "○ Backend Offline (Start Flask API)";
            backendStatus.className = "backend-status offline";
        });

    // 2. Render scan record into UI
    function renderScanResult(prompt, result, timestamp) {
        if (!result) return;

        const score = result.risk_score !== undefined ? result.risk_score : 0;
        const decision = result.decision || "ALLOW";
        const attack = result.attack_type || "Benign";
        const reason = result.reason || "Analysis complete.";

        // Update score & progress
        riskScoreVal.textContent = `${score}%`;
        progressBar.style.width = `${Math.min(100, Math.max(4, score))}%`;

        // Update classes based on risk
        if (decision === "BLOCK" || score >= 80) {
            statusBadge.textContent = "BLOCKED";
            statusBadge.className = "status-badge blocked";
            progressBar.className = "progress-fill blocked";
            riskScoreVal.style.color = "#ef4444";
            decisionVal.style.color = "#ef4444";
        } else if (decision === "WARNING" || score > 30) {
            statusBadge.textContent = "WARNING";
            statusBadge.className = "status-badge warning";
            progressBar.className = "progress-fill warning";
            riskScoreVal.style.color = "#f59e0b";
            decisionVal.style.color = "#f59e0b";
        } else {
            statusBadge.textContent = "SAFE";
            statusBadge.className = "status-badge safe";
            progressBar.className = "progress-fill safe";
            riskScoreVal.style.color = "#10b981";
            decisionVal.style.color = "#38bdf8";
        }

        // Update labels
        attackType.textContent = attack;
        decisionVal.textContent = decision;
        reasonText.textContent = reason;

        if (prompt) {
            scannedPromptText.textContent = prompt.length > 80 ? prompt.substring(0, 80) + "..." : prompt;
        }

        if (timestamp) {
            const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            scanTimestamp.textContent = time;
        } else {
            scanTimestamp.textContent = "Just now";
        }
    }

    // 3. Load previous scan if available
    chrome.runtime.sendMessage({ type: "GET_LAST_SCAN" }, (response) => {
        if (response && response.last_scan) {
            const last = response.last_scan;
            renderScanResult(last.prompt, last.result, last.timestamp);
        }
    });

    // 4. Handle "Scan Current Prompt" button
    scanBtn.addEventListener("click", () => {
        scanBtn.disabled = true;
        scanBtn.innerHTML = "<span>⏳</span> Scanning...";

        chrome.runtime.sendMessage({ type: "SCAN_CURRENT_TAB" }, (response) => {
            scanBtn.disabled = false;
            scanBtn.innerHTML = "<span>🔍</span> Scan Current Prompt";

            if (!response || !response.success) {
                scannedPromptText.textContent = response?.error || "No text found in input box or backend offline.";
                return;
            }

            renderScanResult(response.text, response.data, new Date().toISOString());
        });
    });
});