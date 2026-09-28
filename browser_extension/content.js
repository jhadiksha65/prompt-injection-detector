/**
 * content.js
 * Injected script for capturing prompt input on web LLM platforms (ChatGPT, Gemini, Claude),
 * intercepting malicious submissions before they reach the model, and rendering security overlays.
 */

console.log("[Prompt Injection Detector] Content script initialized on:", window.location.hostname);

// Flag to track whether the current prompt submission was verified and approved
let isSubmissionApproved = false;

// How the currently-pending interception was triggered, so a subsequent
// approved submission can be re-dispatched the same way (Enter key vs.
// clicking a send button) instead of always guessing "click a button".
let lastInterceptionContext = null; // { type: "keydown" | "click", element }

/**
 * Extracts prompt text from various web LLM DOM structures (ChatGPT, Claude, Gemini).
 */
function getPromptText() {
    // 1. Check focused element if active
    const active = document.activeElement;
    if (active) {
        if (active.tagName === "TEXTAREA" || active.tagName === "INPUT") {
            if (active.value && active.value.trim()) return active.value.trim();
        }
        if (active.isContentEditable || active.getAttribute("contenteditable") === "true") {
            const activeText = active.innerText || active.textContent || "";
            if (activeText.trim()) return activeText.trim();
        }
    }

    // 2. Specific ChatGPT prompt container (#prompt-textarea, ProseMirror)
    const chatgptTextarea = document.getElementById("prompt-textarea");
    if (chatgptTextarea) {
        const text = chatgptTextarea.innerText || chatgptTextarea.textContent || (chatgptTextarea.value ? chatgptTextarea.value : "");
        if (text && text.trim()) return text.trim();
    }

    // 3. Any ContentEditable / ProseMirror elements
    const editables = document.querySelectorAll('#prompt-textarea, .ProseMirror, div[contenteditable="true"], p[contenteditable="true"], [contenteditable="true"], [role="textbox"], rich-textarea');
    for (const el of editables) {
        const text = el.innerText || el.textContent || "";
        if (text && text.trim()) return text.trim();
    }

    // 4. Standard textarea fallback
    const textareas = document.querySelectorAll("textarea");
    for (const ta of textareas) {
        if (ta.value && ta.value.trim()) return ta.value.trim();
    }

    return "";
}

/**
 * Creates and renders the Cybersecurity Warning / Block Modal.
 *
 * `backendData` is the full /secure-prompt response (the same verdict
 * contract the web UI uses): the Layer 1 verdict/explanation is nested
 * under `backendData.layer1`, and the combined pipeline outcome is in
 * `backendData.final_decision`. Only Layer 1's own BLOCK decision (the
 * same HIGH/CRITICAL block the web UI shows) prevents the "Proceed"
 * option — Layer 1 is what actually stopped this prompt from reaching
 * the model. The raw prompt is intentionally never rendered here.
 */
function showSecurityModal(backendData, onDismiss) {
    // Remove any existing modal
    const existing = document.getElementById("pid-security-modal-overlay");
    if (existing) existing.remove();

    const layer1 = backendData.layer1 || backendData;
    const overallDecision = backendData.final_decision || layer1.decision || "UNKNOWN";

    const overlay = document.createElement("div");
    overlay.id = "pid-security-modal-overlay";
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(10, 15, 29, 0.85);
        backdrop-filter: blur(8px);
        z-index: 99999999;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #f1f5f9;
    `;

    const isCritical = layer1.risk_level === "CRITICAL";
    const isHigh = layer1.risk_level === "HIGH";
    const isMedium = layer1.risk_level === "MEDIUM" || overallDecision === "WARNING";
    // Only a genuine Layer 1 BLOCK (prompt never reached the AI) removes the
    // "Proceed" option — matches the backend's own decision, never a
    // client-invented security judgement.
    const isBlock = layer1.decision === "BLOCK";

    let headerColor = "#ef4444";
    let badgeBg = "rgba(239, 68, 68, 0.2)";
    let badgeBorder = "#ef4444";
    let modalTitle = "CRITICAL THREAT BLOCKED";

    if (isCritical) {
        headerColor = "#ef4444";
        badgeBg = "rgba(239, 68, 68, 0.2)";
        badgeBorder = "#ef4444";
        modalTitle = "CRITICAL THREAT BLOCKED";
    } else if (isHigh) {
        headerColor = "#f97316";
        badgeBg = "rgba(249, 115, 22, 0.2)";
        badgeBorder = "#f97316";
        modalTitle = "HIGH-RISK PROMPT BLOCKED";
    } else {
        headerColor = "#f59e0b";
        badgeBg = "rgba(245, 158, 11, 0.2)";
        badgeBorder = "#f59e0b";
        modalTitle = "SECURITY ADVISORY WARNING";
    }

    // Section for critical re-auth vs high block vs advisory proceed
    let securityActionHtml = "";
    if (isCritical) {
        // Alert Dispatched Notice (for critical blocked threats)
        const alertHtml = (backendData.alert_status === "SENT" || backendData.email_status === "SENT") ? `
            <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 10px 14px; margin-bottom: 18px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">📧</span>
                <div style="font-size: 12px; color: #93c5fd; line-height: 1.4;">
                    <strong>Alert Dispatched:</strong> Security incident logged and reported to the security team.
                </div>
            </div>
        ` : '';

        securityActionHtml = `
            ${alertHtml}
            <div style="background: #0f172a; border-radius: 8px; padding: 14px; margin-bottom: 18px; border: 1px solid #334155;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span style="font-size: 16px;">🔒</span>
                    <span style="font-size: 13px; font-weight: 700; color: #f1f5f9;">Session Suspended • Re-Authentication</span>
                </div>
                <p style="font-size: 12px; color: #94a3b8; margin-bottom: 10px;">
                    Critical prompt injection attempt detected. Enter authorized credentials to unlock session and override.
                </p>
                <div style="display: flex; gap: 8px;">
                    <input id="pid-auth-pwd" type="password" placeholder="Enter admin password" style="
                        flex: 1;
                        background: #1e293b;
                        border: 1px solid #475569;
                        padding: 8px 12px;
                        border-radius: 6px;
                        color: #fff;
                        font-size: 13px;
                        outline: none;
                    " />
                    <button id="pid-btn-reauth" style="
                        background: #ef4444;
                        color: #fff;
                        border: none;
                        padding: 8px 14px;
                        border-radius: 6px;
                        font-weight: 700;
                        cursor: pointer;
                        font-size: 12px;
                    ">Unlock</button>
                </div>
                <div id="pid-auth-msg" style="font-size: 11px; margin-top: 6px; display: none;"></div>
            </div>
        `;
    } else if (isHigh) {
        // High Risk Blocked (No session suspension)
        const alertHtml = (backendData.alert_status === "SENT" || backendData.email_status === "SENT") ? `
            <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 8px; padding: 10px 14px; margin-bottom: 18px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 18px;">📧</span>
                <div style="font-size: 12px; color: #93c5fd; line-height: 1.4;">
                    <strong>Alert Dispatched:</strong> High-risk security event logged and reported.
                </div>
            </div>
        ` : '';

        securityActionHtml = `
            ${alertHtml}
            <div style="background: rgba(249, 115, 22, 0.1); border: 1px solid rgba(249, 115, 22, 0.3); border-radius: 8px; padding: 12px 14px; margin-bottom: 18px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <span style="font-size: 16px;">⚠️</span>
                    <strong style="font-size: 13px; color: #f97316;">High-Risk Adversarial Input Blocked</strong>
                </div>
                <p style="font-size: 12px; color: #cbd5e1; margin: 0; line-height: 1.4;">
                    This prompt contains high-risk instruction patterns and was blocked by Layer 1 security before reaching the model.
                </p>
            </div>
        `;
    } else {
        // Advisory Warning Note for Medium risk
        securityActionHtml = `
            <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 8px; padding: 12px 14px; margin-bottom: 18px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                    <span style="font-size: 16px;">⚠️</span>
                    <strong style="font-size: 13px; color: #fbbf24;">Security Advisory Notice</strong>
                </div>
                <p style="font-size: 12px; color: #cbd5e1; margin: 0; line-height: 1.4;">
                    Potential prompt injection indicators or elevated risk detected. Review your prompt or click <strong>Proceed with Submission</strong> if this input is intended.
                </p>
            </div>
        `;
    }

    const footerButtonsHtml = isBlock ? `
        <button id="pid-btn-dismiss" style="
            background: #334155;
            color: #f1f5f9;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        ">Cancel & Edit Prompt</button>
    ` : `
        <button id="pid-btn-dismiss" style="
            background: #334155;
            color: #f1f5f9;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        ">Cancel & Edit Prompt</button>
        <button id="pid-btn-proceed" style="
            background: #f59e0b;
            color: #0f172a;
            border: none;
            padding: 10px 18px;
            border-radius: 8px;
            font-weight: 700;
            cursor: pointer;
            transition: background 0.2s;
        ">Proceed with Submission</button>
    `;

    overlay.innerHTML = `
        <div style="
            background: #1e293b;
            border: 2px solid ${badgeBorder};
            border-radius: 16px;
            width: 90%;
            max-width: 520px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
            overflow: hidden;
            animation: pidFadeIn 0.2s ease-out;
        ">
            <!-- Header -->
            <div style="background: ${badgeBg}; border-bottom: 1px solid ${badgeBorder}; padding: 18px 24px; display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px;">🛡️</span>
                    <h3 style="margin: 0; font-size: 18px; font-weight: 700; color: ${headerColor};">
                        ${modalTitle}
                    </h3>
                </div>
                <span style="
                    background: ${badgeBorder};
                    color: ${isBlock ? "#fff" : "#0f172a"};
                    font-size: 12px;
                    font-weight: 800;
                    padding: 4px 10px;
                    border-radius: 20px;
                    text-transform: uppercase;
                "><span id="pid-risk-level-text"></span></span>
            </div>

            <!-- Body -->
            <div style="padding: 24px;">
                <!-- Risk Metric Card -->
                <div style="background: #0f172a; border-radius: 10px; padding: 16px; margin-bottom: 20px; border: 1px solid #334155;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                        <span style="font-size: 13px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Estimated Threat Risk</span>
                        <span style="font-size: 22px; font-weight: 800; color: ${headerColor};"><span id="pid-risk-score-text"></span> / 100</span>
                    </div>
                    <!-- Progress Bar -->
                    <div style="width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden;">
                        <div id="pid-risk-bar-fill" style="width: 0%; height: 100%; background: ${headerColor}; transition: width 0.4s ease;"></div>
                    </div>
                </div>

                <!-- Threat Details -->
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 12px; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">Detected Attack Vector</div>
                    <div id="pid-attack-type-text" style="font-size: 15px; color: #f8fafc; font-weight: 600;"></div>
                </div>

                <div style="margin-bottom: 16px;">
                    <div style="font-size: 12px; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">Security Explanation</div>
                    <div id="pid-reason-text" style="font-size: 14px; color: #cbd5e1; line-height: 1.5; background: #0f172a; padding: 12px; border-radius: 8px; border-left: 4px solid ${badgeBorder};"></div>
                </div>

                <!-- Security Action Section (Re-Auth or Advisory) -->
                ${securityActionHtml}

                <!-- Footer Actions -->
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    ${footerButtonsHtml}
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // All backend-derived dynamic text is written via textContent, never
    // interpolated into the innerHTML template above — this is the only
    // place any of these values touch the DOM.
    document.getElementById("pid-risk-level-text").textContent = layer1.risk_level || "UNKNOWN";
    const riskScoreValue = Number(layer1.risk_score) || 0;
    document.getElementById("pid-risk-score-text").textContent = String(riskScoreValue);
    document.getElementById("pid-risk-bar-fill").style.width = `${Math.min(100, Math.max(5, riskScoreValue))}%`;
    document.getElementById("pid-attack-type-text").textContent = layer1.attack_type || "Unknown";
    document.getElementById("pid-reason-text").textContent = layer1.reason || "No further explanation provided.";

    document.getElementById("pid-btn-dismiss").addEventListener("click", () => {
        overlay.remove();
        if (onDismiss) onDismiss();
    });

    const proceedBtn = document.getElementById("pid-btn-proceed");
    if (proceedBtn) {
        proceedBtn.addEventListener("click", () => {
            isSubmissionApproved = true;
            overlay.remove();
            triggerOriginalSubmit();
        });
    }

    const reauthBtn = document.getElementById("pid-btn-reauth");
    if (reauthBtn) {
        reauthBtn.addEventListener("click", () => {
            const pwd = document.getElementById("pid-auth-pwd").value.trim();
            const msg = document.getElementById("pid-auth-msg");
            
            msg.style.display = "block";
            msg.style.color = "#cbd5e1";
            msg.textContent = "⏳ Verifying with security backend...";

            chrome.runtime.sendMessage({
                type: "UNLOCK_SESSION",
                password: pwd
            }, (response) => {
                if (response && response.success) {
                    msg.style.color = "#10b981";
                    msg.textContent = "✅ Identity verified! Session unlocked.";
                    setTimeout(() => {
                        overlay.remove();
                    }, 1000);
                } else {
                    msg.style.color = "#ef4444";
                    const errMsg = response?.error || "Invalid credentials. Access remains locked.";
                    msg.textContent = `❌ ${errMsg}`;
                }
            });
        });
    }
}

/**
 * Shows a subtle floating toast for verified safe prompts.
 */
function showSafeToast(score) {
    const existing = document.getElementById("pid-safe-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = "pid-safe-toast";
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #065f46;
        color: #ecfdf5;
        border: 1px solid #10b981;
        padding: 10px 16px;
        border-radius: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        font-size: 13px;
        font-weight: 600;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    // No dynamic/untrusted content here — the score is our own numeric
    // risk score — but built via safe DOM APIs rather than innerHTML anyway.
    const icon = document.createElement("span");
    icon.textContent = "🛡️";
    const label = document.createTextNode(` Prompt Verified Safe • Risk ${Number(score) || 0}/100`);
    toast.appendChild(icon);
    toast.appendChild(label);
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.5s ease";
        setTimeout(() => toast.remove(), 500);
    }, 2500);
}

/**
 * Shows a fail-closed notice: the backend could not be reached, so the
 * prompt was withheld rather than assumed safe. No auto-submission happens.
 */
function showBackendUnavailableNotice() {
    const existing = document.getElementById("pid-safe-toast");
    if (existing) existing.remove();

    const toast = document.createElement("div");
    toast.id = "pid-safe-toast";
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #7f1d1d;
        color: #fee2e2;
        border: 1px solid #ef4444;
        padding: 10px 16px;
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        font-size: 13px;
        font-weight: 600;
        z-index: 999999;
        display: flex;
        align-items: center;
        gap: 8px;
        max-width: 320px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    const icon = document.createElement("span");
    icon.textContent = "⛔";
    const label = document.createElement("span");
    label.textContent = "Security check unavailable — prompt was NOT submitted. Protection could not be confirmed.";
    toast.appendChild(icon);
    toast.appendChild(label);
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.5s ease";
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

/**
 * Triggers prompt submission after inspection passes, replaying it the same
 * way it was originally triggered (Enter key vs. a send button click).
 */
function triggerOriginalSubmit() {
    if (lastInterceptionContext && lastInterceptionContext.type === "keydown" && lastInterceptionContext.element) {
        const syntheticEnter = new KeyboardEvent("keydown", {
            key: "Enter",
            code: "Enter",
            bubbles: true,
            cancelable: true
        });
        lastInterceptionContext.element.dispatchEvent(syntheticEnter);
        return;
    }

    // Look for standard submit button or trigger form submit
    const sendButton = document.querySelector(
        'button[data-testid="send-button"], button[aria-label="Send prompt"], button[aria-label="Send Message"], button#send-button'
    );
    if (sendButton) {
        sendButton.click();
    }
}

function approveAndResubmit() {
    isSubmissionApproved = true;
    triggerOriginalSubmit();
}

/**
 * Intercepts prompt submission and queries the background script.
 *
 * CRITICAL ordering: preventDefault()/stopPropagation() are called
 * synchronously, before the asynchronous backend check begins. The
 * verification is inherently async (content script -> background service
 * worker -> Flask backend), so the submission must never be allowed to
 * proceed while that check is still in flight — otherwise the real site's
 * own submit handler races ahead of the security verdict.
 */
function handlePromptInterception(e) {
    if (isSubmissionApproved) {
        isSubmissionApproved = false;
        return; // Allow the just-approved, re-dispatched submission through
    }

    const promptText = getPromptText();
    if (!promptText || promptText.length < 3) return;

    // Prevent the default action FIRST, synchronously, before any await.
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    lastInterceptionContext = { type: e.type, element: e.target };

    // Delegates to the background service worker, which calls the real
    // backend /secure-prompt pipeline. No security decision is made here.
    chrome.runtime.sendMessage({
        type: "CHECK_PROMPT",
        prompt: promptText
    }, (response) => {
        if (!response || !response.success || !response.data) {
            // Fail CLOSED: the prompt was never sent to the AI, and it stays
            // that way — we do not fall back to "assume safe".
            showBackendUnavailableNotice();
            return;
        }

        const data = response.data;
        const layer1 = data.layer1 || data;
        const overallDecision = data.final_decision || layer1.decision || "UNKNOWN";

        if (layer1.decision === "BLOCK" || overallDecision !== "ALLOW") {
            // Layer 1 BLOCK (prompt never reached the AI) or any non-clean-
            // ALLOW combined verdict (WARNING/MASK/ERROR) surfaces the same
            // explanation/verdict modal the web UI shows, rather than
            // silently deciding on the client.
            showSecurityModal(data, () => {
                lastInterceptionContext = null;
            });
        } else {
            showSafeToast(layer1.risk_score);
            approveAndResubmit();
        }
    });
}

// 1. Intercept Enter Key in inputs
document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey && !e.altKey) {
        const active = document.activeElement;
        if (active && (active.isContentEditable || active.tagName === "TEXTAREA")) {
            handlePromptInterception(e);
        }
    }
}, true); // Use capture phase

// 2. Intercept Click on Submit Buttons
document.addEventListener("click", (e) => {
    const target = e.target;
    const button = target.closest(
        'button[data-testid="send-button"], button[aria-label="Send prompt"], button[aria-label="Send Message"], button#send-button'
    );
    if (button) {
        handlePromptInterception(e);
    }
}, true);

// 3. Respond to Popup queries
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "GET_CURRENT_PROMPT") {
        const text = getPromptText();
        sendResponse({ text: text });
    }
});