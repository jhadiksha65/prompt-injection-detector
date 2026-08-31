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
    const llmCalled = document.getElementById("llmCalled");
    const bannerReason = document.getElementById("bannerReason");

    const API_BASE_URL = window.location.origin;

    try {
        const response = await fetch(`${API_BASE_URL}/secure-prompt`, {
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
        llmCalled.textContent = data.llm_called ? "YES" : "NO";
        l2Decision.textContent = l2.decision || "SAFE";

        // Format Banner Reason
        if (data.final_decision === "BLOCK") {
            if (l1.decision === "BLOCK" || l1.risk_level === "CRITICAL") {
                bannerReason.textContent = "Reason: Blocked by Layer 1 before LLM generation";
            } else {
                bannerReason.textContent = `Reason: Sensitive information detected in generated response (${l2.reason || "Confidential leakage"})`;
            }
        } else if (data.final_decision === "MASK") {
            bannerReason.textContent = "Reason: Response sanitized - sensitive credentials masked by Layer 2";
        } else {
            bannerReason.textContent = "Reason: Response validated and verified safe.";
        }

        if (data.final_decision === "BLOCK") {
            // Check if Layer 1 or Layer 2 caused the block
            if (l1.decision === "BLOCK" || l1.risk_level === "CRITICAL" || l1.risk_level === "HIGH") {
                const isCritical = (l1.risk_level === "CRITICAL");
                const levelName = isCritical ? "CRITICAL" : "HIGH";
                const badgeClass = isCritical ? "risk-badge critical" : "risk-badge high";
                const borderColor = isCritical ? "#ef4444" : "#f97316";
                const bgAlpha = isCritical ? "rgba(239, 68, 68, 0.1)" : "rgba(249, 115, 22, 0.1)";
                const titleText = isCritical ? "🚨 CRITICAL THREAT BLOCKED" : "⚠️ HIGH-RISK PROMPT BLOCKED";

                bannerRiskBadge.textContent = `${levelName} / BLOCKED`;
                bannerRiskBadge.className = badgeClass;
                
                const warningHtml = `
                    <div class="security-warning-card ${isCritical ? 'critical-block' : 'high-block'}" style="border: 2px solid ${borderColor}; background: ${bgAlpha}; padding: 15px; border-radius: 8px; margin: 10px 0; font-family: sans-serif;">
                        <h4 style="color: ${borderColor}; margin: 0 0 10px 0; display: flex; align-items: center; gap: 8px;">${titleText}</h4>
                        <p style="margin: 4px 0; font-size: 14px;"><strong>Prompt blocked</strong></p>
                        <p style="margin: 4px 0; font-size: 13px;"><strong>Risk Level:</strong> ${levelName}</p>
                        <p style="margin: 4px 0; font-size: 13px;"><strong>Risk Score:</strong> ${l1.risk_score || 0}%</p>
                        <p style="margin: 4px 0; font-size: 13px;"><strong>Attack Type:</strong> ${l1.attack_type || "Prompt Injection"}</p>
                        <p style="margin: 6px 0; padding: 6px; font-size: 13px; background: rgba(0,0,0,0.2); border-left: 3px solid ${borderColor}; color: #f8fafc;"><strong>Reason:</strong> ${l1.reason || "High adversarial risk detected."}</p>
                        <p style="margin: 4px 0; font-size: 13px;"><strong>Email:</strong> ${data.email_status || 'NOT_CONFIGURED'}</p>
                        <p style="margin: 4px 0; font-size: 13px;"><strong>SMS:</strong> ${data.sms_status || 'NOT_CONFIGURED'}</p>
                    </div>
                `;
                appendMessageHtml("assistant blocked", isCritical ? "🚨" : "🛡️", warningHtml);

                if (data.requires_reauth && isCritical) {
                    openReauthModal(data);
                }
            } else {
                // Layer 2 Block
                bannerRiskBadge.textContent = "CRITICAL / BLOCKED";
                bannerRiskBadge.className = "risk-badge critical";
                
                const warningHtml = `
                    <div class="security-warning-card layer2-block" style="border: 2px solid #ef4444; background: rgba(239, 68, 68, 0.1); padding: 15px; border-radius: 8px; margin: 10px 0; font-family: sans-serif;">
                        <h4 style="color: #ef4444; margin: 0 0 10px 0; display: flex; align-items: center; gap: 8px;">⚠️ RESPONSE BLOCKED</h4>
                        <p style="margin: 4px 0; font-size: 14px;">The AI-generated response failed security validation.</p>
                        <p style="margin: 4px 0; font-size: 13px; color: #ef4444;">Do not display unsafe response content.</p>
                        <p style="margin: 4px 0; font-size: 13px;"><strong>Email:</strong> ${data.email_status || 'NOT_CONFIGURED'}</p>
                        <p style="margin: 4px 0; font-size: 13px;"><strong>SMS:</strong> ${data.sms_status || 'NOT_CONFIGURED'}</p>
                    </div>
                `;
                appendMessageHtml("assistant blocked", "🛡️", warningHtml);
            }
        } else if (data.final_decision === "WARNING" || l1.decision === "WARNING" || l1.risk_level === "MEDIUM") {
            bannerRiskBadge.textContent = "MEDIUM / WARNING";
            bannerRiskBadge.className = "risk-badge medium";
            bannerReason.textContent = `Reason: Security Advisory — ${l1.reason || "Moderate risk indicators detected."}`;

            const warningHtml = `
                <div class="security-warning-card medium-warning" style="border: 2px solid #f59e0b; background: rgba(245, 158, 11, 0.1); padding: 15px; border-radius: 8px; margin: 10px 0; font-family: sans-serif;">
                    <h4 style="color: #f59e0b; margin: 0 0 10px 0; display: flex; align-items: center; gap: 8px;">⚠️ SECURITY ADVISORY</h4>
                    <p style="margin: 4px 0; font-size: 14px;"><strong>Elevated Risk Detected (${l1.risk_score || 0}%)</strong></p>
                    <p style="margin: 4px 0; font-size: 13px;"><strong>Risk Level:</strong> MEDIUM</p>
                    <p style="margin: 4px 0; font-size: 13px;"><strong>Attack Type:</strong> ${l1.attack_type || "Advisory"}</p>
                    <p style="margin: 6px 0; padding: 6px; font-size: 13px; background: rgba(0,0,0,0.2); border-left: 3px solid #f59e0b; color: #f8fafc;"><strong>Reason:</strong> ${l1.reason || "Review prompt before proceeding."}</p>
                </div>
            `;
            appendMessageHtml("assistant warning", "🛡️", warningHtml);
            appendMessage("assistant", "🤖", data.response);
        } else if (data.final_decision === "MASK") {
            bannerRiskBadge.textContent = "SANITIZED (L2)";
            bannerRiskBadge.className = "risk-badge low";
            appendMessage("assistant masked", "🛡️", "⚠️ RESPONSE SANITIZED:\n" + data.response);
        } else {
            bannerRiskBadge.textContent = "VERIFIED SAFE";
            bannerRiskBadge.className = "risk-badge low";
            appendMessage("assistant safe-header", "🛡️", "✓ SAFE");
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

function appendMessageHtml(roleClass, avatar, htmlContent) {
    const container = document.getElementById("chatContainer");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${roleClass}`;
    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-body">
            ${htmlContent}
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
