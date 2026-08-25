/**
 * app.js
 * Client-side script for Secure AI Assistant Demo application.
 * Communicates with POST /secure-prompt and renders live dual-layer diagnostic status
 * as well as triggering automated Alert and Credential Re-Authentication modal on threats.
 */

function setPrompt(text) {
    const input = document.getElementById("promptInput");
    input.value = text;
    input.focus();
}

async function handleSend(e) {
    e.preventDefault();
    const input = document.getElementById("promptInput");
    const prompt = input.value.trim();
    if (!prompt) return;

    input.value = "";
    const sendBtn = document.getElementById("sendBtn");
    sendBtn.disabled = true;
    sendBtn.innerHTML = "<span>Scanning...</span>";

    // Append User Message to Chat
    appendMessage("user", "👤", prompt);

    const banner = document.getElementById("securityBanner");
    const bannerRiskBadge = document.getElementById("bannerRiskBadge");
    const l1Decision = document.getElementById("l1Decision");
    const l1Score = document.getElementById("l1Score");
    const l1Attack = document.getElementById("l1Attack");
    const l2Decision = document.getElementById("l2Decision");
    const bannerReason = document.getElementById("bannerReason");

    try {
        const response = await fetch("/secure-prompt", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ prompt: prompt })
        });

        const data = await response.json();

        // Update Security Diagnostic Banner
        banner.style.display = "block";
        const l1 = data.layer1 || {};
        const l2 = data.layer2 || {};

        l1Decision.textContent = l1.decision || "ALLOW";
        l1Score.textContent = `${l1.risk_score || 0}%`;
        l1Attack.textContent = l1.attack_type || "None";
        l2Decision.textContent = l2.decision || (data.llm_called ? "SAFE" : "N/A (Blocked)");
        bannerReason.textContent = `L1 Reason: ${l1.reason || "Safe"} | L2: ${l2.reason || "Validated"}`;

        if (data.final_decision === "BLOCK") {
            bannerRiskBadge.textContent = "CRITICAL / BLOCKED";
            bannerRiskBadge.className = "risk-badge critical";
            appendMessage("assistant blocked", "🛡️", data.response || "Request blocked by security layer.");

            // Trigger Alert & Credential Re-Authentication Modal
            if (data.requires_reauth) {
                openReauthModal(data);
            }
        } else if (data.final_decision === "MASK") {
            bannerRiskBadge.textContent = "SANITIZED (L2)";
            bannerRiskBadge.className = "risk-badge low";
            appendMessage("assistant masked", "🛡️", data.response);
        } else {
            bannerRiskBadge.textContent = "VERIFIED SAFE";
            bannerRiskBadge.className = "risk-badge low";
            appendMessage("assistant", "🤖", data.response);
        }

    } catch (err) {
        console.error("API error:", err);
        appendMessage("assistant blocked", "⚠️", "Failed to connect to Security API backend.");
    } finally {
        sendBtn.disabled = false;
        sendBtn.innerHTML = "<span>Send Prompt</span><span class='arrow'>➤</span>";
    }
}

function appendMessage(roleClass, avatar, text) {
    const container = document.getElementById("chatContainer");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${roleClass}`;
    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-body">
            <p>${escapeHTML(text).replace(/\n/g, "<br/>")}</p>
        </div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

// -------------------------------------------------------------
// Security Threat & Re-Authentication Modal Handlers
// -------------------------------------------------------------
function openReauthModal(data) {
    const modal = document.getElementById("reauthModal");
    const reqId = document.getElementById("modalReqId");
    const attackType = document.getElementById("modalAttackType");
    const riskScore = document.getElementById("modalRiskScore");
    const reason = document.getElementById("modalReason");
    const errorDiv = document.getElementById("reauthError");

    errorDiv.style.display = "none";
    reqId.textContent = data.request_id || "REQ-CRITICAL";
    attackType.textContent = data.layer1?.attack_type || "Adversarial Prompt Injection";
    riskScore.textContent = `${data.layer1?.risk_score || 95}% (${data.layer1?.risk_level || "CRITICAL"})`;
    reason.textContent = data.layer1?.reason || "High-severity prompt injection pattern detected.";

    modal.style.display = "flex";
    document.getElementById("reauthPassword").value = "";
    document.getElementById("reauthPassword").focus();
}

function closeReauthModal() {
    document.getElementById("reauthModal").style.display = "none";
}

async function submitReauth(e) {
    e.preventDefault();
    const username = document.getElementById("reauthUsername").value.trim();
    const password = document.getElementById("reauthPassword").value.trim();
    const errorDiv = document.getElementById("reauthError");
    const submitBtn = document.getElementById("btnSubmitReauth");

    submitBtn.disabled = true;
    submitBtn.textContent = "Verifying...";
    errorDiv.style.display = "none";

    try {
        const response = await fetch("/api/unlock", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: username, password: password })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            closeReauthModal();
            appendMessage("assistant", "✅", `Identity verified for user '${username}'. Session unlocked & security controls restored.`);
        } else {
            errorDiv.textContent = result.error || "Authentication failed. Invalid password.";
            errorDiv.style.display = "block";
        }
    } catch (err) {
        errorDiv.textContent = "Error communicating with authentication service.";
        errorDiv.style.display = "block";
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Verify & Restore Session";
    }
}
