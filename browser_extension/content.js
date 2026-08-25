/**
 * content.js
 * Injected script for capturing prompt input on web LLM platforms (ChatGPT, Gemini, Claude),
 * intercepting malicious submissions before they reach the model, and rendering security overlays.
 */

console.log("[Prompt Injection Detector] Content script initialized on:", window.location.hostname);

// Flag to track whether the current prompt submission was verified and approved
let isSubmissionApproved = false;

/**
 * Extracts prompt text from various web LLM DOM structures.
 */
function getPromptText() {
    // 1. ContentEditable input (ChatGPT, Claude, Gemini)
    const contentEditable = document.querySelector('div[contenteditable="true"], div#prompt-textarea, [data-placeholder]');
    if (contentEditable) {
        const text = contentEditable.innerText || contentEditable.textContent || "";
        if (text.trim()) return text.trim();
    }

    // 2. Textarea fallback
    const textarea = document.querySelector("textarea");
    if (textarea && textarea.value) {
        return textarea.value.trim();
    }

    return "";
}

/**
 * Creates and renders the Cybersecurity Warning / Block Modal.
 */
function showSecurityModal(result, rawPrompt, onDismiss) {
    // Remove any existing modal
    const existing = document.getElementById("pid-security-modal-overlay");
    if (existing) existing.remove();

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

    const isBlock = result.decision === "BLOCK";
    const headerColor = isBlock ? "#ef4444" : "#f59e0b";
    const badgeBg = isBlock ? "rgba(239, 68, 68, 0.2)" : "rgba(245, 158, 11, 0.2)";
    const badgeBorder = isBlock ? "#ef4444" : "#f59e0b";

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
                        ${isBlock ? "PROMPT INJECTION BLOCKED" : "SECURITY ADVISORY WARNING"}
                    </h3>
                </div>
                <span style="
                    background: ${badgeBorder};
                    color: #fff;
                    font-size: 12px;
                    font-weight: 800;
                    padding: 4px 10px;
                    border-radius: 20px;
                    text-transform: uppercase;
                ">${result.risk_level}</span>
            </div>

            <!-- Body -->
            <div style="padding: 24px;">
                <!-- Risk Metric Card -->
                <div style="background: #0f172a; border-radius: 10px; padding: 16px; margin-bottom: 20px; border: 1px solid #334155;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
                        <span style="font-size: 13px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Estimated Threat Risk</span>
                        <span style="font-size: 22px; font-weight: 800; color: ${headerColor};">${result.risk_score} / 100</span>
                    </div>
                    <!-- Progress Bar -->
                    <div style="width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden;">
                        <div style="width: ${Math.min(100, Math.max(5, result.risk_score))}%; height: 100%; background: ${headerColor}; transition: width 0.4s ease;"></div>
                    </div>
                </div>

                <!-- Threat Details -->
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 12px; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">Detected Attack Vector</div>
                    <div style="font-size: 15px; color: #f8fafc; font-weight: 600;">${result.attack_type}</div>
                </div>

                <div style="margin-bottom: 20px;">
                    <div style="font-size: 12px; color: #64748b; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">Security Explanation</div>
                    <div style="font-size: 14px; color: #cbd5e1; line-height: 1.5; background: #0f172a; padding: 12px; border-radius: 8px; border-left: 4px solid ${badgeBorder};">
                        ${result.reason}
                    </div>
                </div>

                <!-- Footer Actions -->
                <div style="display: flex; gap: 12px; justify-content: flex-end;">
                    <button id="pid-btn-dismiss" style="
                        background: #334155;
                        color: #f1f5f9;
                        border: none;
                        padding: 10px 18px;
                        border-radius: 8px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: background 0.2s;
                    ">Edit Prompt</button>
                    ${!isBlock ? `
                    <button id="pid-btn-override" style="
                        background: ${headerColor};
                        color: #0f172a;
                        border: none;
                        padding: 10px 18px;
                        border-radius: 8px;
                        font-weight: 700;
                        cursor: pointer;
                    ">Proceed Anyway</button>` : ''}
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    document.getElementById("pid-btn-dismiss").addEventListener("click", () => {
        overlay.remove();
        if (onDismiss) onDismiss();
    });

    const overrideBtn = document.getElementById("pid-btn-override");
    if (overrideBtn) {
        overrideBtn.addEventListener("click", () => {
            isSubmissionApproved = true;
            overlay.remove();
            triggerOriginalSubmit();
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
    toast.innerHTML = `<span>🛡️</span> Prompt Verified Safe • Risk ${score}/100`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transition = "opacity 0.5s ease";
        setTimeout(() => toast.remove(), 500);
    }, 2500);
}

/**
 * Triggers prompt submission after inspection passes.
 */
function triggerOriginalSubmit() {
    // Look for standard submit button or trigger form submit
    const sendButton = document.querySelector(
        'button[data-testid="send-button"], button[aria-label="Send prompt"], button[aria-label="Send Message"], button#send-button'
    );
    if (sendButton) {
        sendButton.click();
    }
}

/**
 * Intercepts prompt submission and queries the background script.
 */
function handlePromptInterception(e) {
    if (isSubmissionApproved) {
        isSubmissionApproved = false;
        return; // Allow approved submission through
    }

    const promptText = getPromptText();
    if (!promptText || promptText.length < 3) return;

    // Check with background service worker
    chrome.runtime.sendMessage({
        type: "CHECK_PROMPT",
        prompt: promptText
    }, (response) => {
        if (!response || !response.data) return;

        const data = response.data;

        if (data.decision === "BLOCK") {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            showSecurityModal(data, promptText);
        } else if (data.decision === "WARNING") {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            showSecurityModal(data, promptText);
        } else {
            showSafeToast(data.risk_score);
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