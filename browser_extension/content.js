/**
 * content.js
 * Injected script for capturing prompt input on web LLM platforms (ChatGPT, Gemini, Claude),
 * intercepting malicious submissions before they reach the model, and rendering security overlays.
 */

console.log("[Prompt Injection Detector] Content script initialized on:", window.location.hostname);

// Flag to track whether the current prompt submission was verified and approved
let isSubmissionApproved = false;
let isCheckingPrompt = false;
let lastKnownPromptText = "";

// How the currently-pending interception was triggered, so a subsequent
// approved submission can be re-dispatched the same way (Enter key vs.
// clicking a send button) instead of always guessing "click a button".
let lastInterceptionContext = null; // { type: "keydown" | "click" | "submit", element }

const KNOWN_PLACEHOLDERS = [
    "message chatgpt",
    "message chatgpt...",
    "ask anything",
    "ask anything...",
    "what's on your mind",
    "what's on your mind?",
    "message claude",
    "message claude...",
    "reply to claude",
    "reply to claude...",
    "how can claude help you today",
    "how can claude help you today?",
    "ask gemini",
    "ask gemini...",
    "type a message",
    "type a message...",
    "type something",
    "type something...",
    "enter a prompt here",
    "enter a prompt here..."
];

/**
 * Detects whether a text fragment is merely an application placeholder or watermark.
 */
function isPlaceholderText(str) {
    if (!str) return true;
    const clean = str.trim().toLowerCase();
    if (clean.length === 0) return true;
    return KNOWN_PLACEHOLDERS.some(pl => clean === pl || clean.startsWith(pl));
}

/**
 * Checks whether an element is an input, textarea, or contenteditable editor.
 */
function isPromptInputElement(el) {
    if (!el) return false;
    const elem = el.nodeType === 3 ? el.parentElement : el;
    if (!elem) return false;
    if (elem.isContentEditable || (typeof elem.getAttribute === "function" && elem.getAttribute("contenteditable") === "true")) return true;
    if (elem.tagName === "TEXTAREA" || elem.tagName === "INPUT") return true;
    if (typeof elem.closest === "function" && elem.closest('[contenteditable="true"], #prompt-textarea, textarea, rich-textarea, .ProseMirror, [role="textbox"]')) return true;
    return false;
}

/**
 * Extracts prompt text cleanly from an element, supporting ProseMirror paragraphs,
 * textareas, inputs, and contenteditable containers across LLM platforms.
 */
function extractCleanElementText(el) {
    if (!el) return "";

    // 1. Textarea / Input value
    if (typeof el.value === "string" && el.value.trim()) {
        const val = el.value.trim();
        if (!isPlaceholderText(val)) return val;
    }

    // 2. ProseMirror / ContentEditable paragraph structure (ChatGPT, Claude, etc.)
    const paragraphs = el.querySelectorAll ? el.querySelectorAll("p, div.paragraph, div.ProseMirror-prompt") : [];
    if (paragraphs && paragraphs.length > 0) {
        const lines = [];
        for (const p of paragraphs) {
            // Ignore placeholder paragraphs
            if (p.classList && p.classList.contains("placeholder") && !p.textContent.trim()) {
                continue;
            }
            const pt = (p.textContent || p.innerText || "").trim();
            if (pt && !isPlaceholderText(pt)) {
                lines.push(pt);
            }
        }
        if (lines.length > 0) {
            return lines.join("\n").trim();
        }
    }

    // 3. Clone contenteditable to safely remove placeholder nodes
    if (el.isContentEditable || el.getAttribute("contenteditable") === "true") {
        try {
            const clone = el.cloneNode(true);
            const placeholders = clone.querySelectorAll('.placeholder, [data-placeholder]');
            placeholders.forEach(pl => {
                if (isPlaceholderText(pl.textContent)) pl.remove();
            });
            const text = (clone.innerText || clone.textContent || "").trim();
            if (text && !isPlaceholderText(text)) {
                return text;
            }
        } catch (_) {}
    }

    // 4. Fallback to textContent and innerText
    // In Chromium, innerText on unfocused/blurred tabs or ProseMirror divs
    // can return "\n" or empty string while textContent contains the text.
    const tc = (el.textContent || "").trim();
    const it = (el.innerText || "").trim();

    let candidate = "";
    if (tc && !isPlaceholderText(tc)) {
        candidate = tc;
    } else if (it && !isPlaceholderText(it)) {
        candidate = it;
    }

    return candidate;
}

/**
 * Extracts prompt text from various web LLM DOM structures (ChatGPT, Claude, Gemini).
 */
function getPromptText() {
    // 1. Check focused element if active and inside an editor
    const active = document.activeElement;
    if (active && active !== document.body && active !== document.documentElement) {
        const container = active.isContentEditable
            ? (active.closest('#prompt-textarea, [contenteditable="true"], .ProseMirror') || active)
            : active;
        if (isPromptInputElement(container)) {
            const activeText = extractCleanElementText(container);
            if (activeText && activeText.length > 0) return activeText;
        }
    }

    // 2. Specific ChatGPT & web LLM prompt container selectors
    const selectors = [
        '#prompt-textarea',
        '[data-testid="prompt-textarea"]',
        'div#prompt-textarea[contenteditable="true"]',
        'div.ProseMirror[contenteditable="true"]',
        'form div.ProseMirror',
        'div.ProseMirror',
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"]',
        '#chat-textarea',
        'form textarea',
        'textarea[data-id="root"]',
        'textarea[placeholder*="Ask" i]',
        'textarea[placeholder*="Send" i]',
        'textarea',
        'rich-textarea',
        '[role="textbox"]'
    ];

    for (const sel of selectors) {
        try {
            const elements = document.querySelectorAll(sel);
            for (const el of elements) {
                const text = extractCleanElementText(el);
                if (text && text.length > 0) return text;
            }
        } catch (_) {}
    }

    // 3. Fallback to continuously-tracked input text if DOM was just cleared
    if (lastKnownPromptText && lastKnownPromptText.trim().length > 0) {
        return lastKnownPromptText.trim();
    }

    return "";
}

/**
 * Creates and renders the Cybersecurity Warning / Block Modal.
 *
 * Visually unified with the Analyzer's blocking dialog:
 * - Red ⛔ icon and authoritative headline
 * - Viewport-constrained modal card with smooth internal scrolling
 * - Scanned input quote preview
 * - 3-cell metric grid (Threat Source, Attack Vector, Risk score & badge)
 * - Threat evidence section (when available)
 * - Why it was blocked explanation box
 * - Clean action buttons ("Try a Safer Prompt" / "Close")
 * - No session re-authentication or password prompts
 */
function showSecurityModal(backendData, onDismiss, promptText = "") {
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
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(6px);
        z-index: 99999999;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #0f172a;
        padding: 16px;
        box-sizing: border-box;
    `;

    const isCritical = layer1.risk_level === "CRITICAL";
    const isHigh = layer1.risk_level === "HIGH";
    const isBlock = layer1.decision === "BLOCK" || isCritical || isHigh;

    let modalIcon = "⛔";
    let modalTitle = "Prompt Blocked Before Reaching the AI";
    let modalSubtitle = "This prompt was not sent to the AI model. Our security layer identified it before generation began.";
    let badgeBg = "#fef2f2";
    let badgeColor = "#991b1b";
    let badgeBorder = "#fecaca";
    let riskBarColor = "#ef4444";
    let reasonBg = "#fef2f2";
    let reasonColor = "#991b1b";
    let reasonBorder = "#fecaca";

    if (isCritical) {
        modalIcon = "⛔";
        modalTitle = "Prompt Blocked Before Reaching the AI";
        modalSubtitle = "This prompt was not sent to the AI model. Our security layer identified it before generation began.";
        badgeBg = "#fef2f2";
        badgeColor = "#991b1b";
        badgeBorder = "#fecaca";
        riskBarColor = "#ef4444";
        reasonBg = "#fef2f2";
        reasonColor = "#991b1b";
        reasonBorder = "#fecaca";
    } else if (isHigh) {
        modalIcon = "⛔";
        modalTitle = "Prompt Blocked Before Reaching the AI";
        modalSubtitle = "This prompt was not sent to the AI model. Our security layer identified it before generation began.";
        badgeBg = "#fff7ed";
        badgeColor = "#9a3412";
        badgeBorder = "#ffedd5";
        riskBarColor = "#f97316";
        reasonBg = "#fff7ed";
        reasonColor = "#9a3412";
        reasonBorder = "#fed7aa";
    } else {
        modalIcon = "⚠️";
        modalTitle = "Security Advisory Notice";
        modalSubtitle = "Potential prompt injection indicators detected before submission. Review findings below before proceeding.";
        badgeBg = "#fffbeb";
        badgeColor = "#92400e";
        badgeBorder = "#fde68a";
        riskBarColor = "#f59e0b";
        reasonBg = "#fffbeb";
        reasonColor = "#92400e";
        reasonBorder = "#fde68a";
    }

    const footerButtonsHtml = isBlock ? `
        <button id="pid-btn-dismiss" style="
            background: #0f172a;
            color: #ffffff;
            border: none;
            padding: 9px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.15s ease;
        ">Try a Safer Prompt</button>
        <button id="pid-btn-close" style="
            background: #ffffff;
            color: #0f172a;
            border: 1px solid #e2e8f0;
            padding: 9px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s ease;
        ">Close</button>
    ` : `
        <button id="pid-btn-dismiss" style="
            background: #ffffff;
            color: #0f172a;
            border: 1px solid #e2e8f0;
            padding: 9px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s ease;
        ">Cancel & Edit Prompt</button>
        <button id="pid-btn-proceed" style="
            background: #0f172a;
            color: #ffffff;
            border: none;
            padding: 9px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.15s ease;
        ">Proceed with Submission</button>
    `;

    overlay.innerHTML = `
        <div style="
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            width: 90%;
            max-width: 540px;
            max-height: min(88vh, 660px);
            box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.15), 0 8px 10px -6px rgba(15, 23, 42, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-sizing: border-box;
            text-align: left;
        ">
            <!-- Pinned Header -->
            <div style="
                flex-shrink: 0;
                padding: 20px 24px 14px 24px;
                border-bottom: 1px solid #e2e8f0;
                text-align: center;
                background: #ffffff;
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 4px;
            ">
                <div style="font-size: 28px; line-height: 1;" aria-hidden="true">${modalIcon}</div>
                <h3 style="margin: 4px 0 0 0; font-size: 17px; font-weight: 700; color: #0f172a; letter-spacing: -0.01em;">
                    ${modalTitle}
                </h3>
                <p style="margin: 0; font-size: 12.5px; color: #64748b; line-height: 1.45; max-width: 440px;">
                    ${modalSubtitle}
                </p>
            </div>

            <!-- Scrollable Body -->
            <div style="
                flex: 1 1 auto;
                overflow-y: auto;
                min-height: 0;
                padding: 14px 24px;
                display: flex;
                flex-direction: column;
                gap: 12px;
                box-sizing: border-box;
                overscroll-behavior: contain;
            ">
                <!-- Scanned Input Section -->
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;">Scanned Input</span>
                    <div style="
                        background: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        padding: 9px 12px;
                        max-height: 96px;
                        overflow-y: auto;
                    ">
                        <div id="pid-scanned-prompt-text" style="
                            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                            font-size: 12px;
                            line-height: 1.45;
                            color: #1e293b;
                            white-space: pre-wrap;
                            word-break: break-word;
                        "></div>
                    </div>
                </div>

                <!-- Threat & Risk Breakdown Grid (3 cells matching Analyzer) -->
                <div style="
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 8px;
                ">
                    <!-- Cell 1: Threat Source -->
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 10px; display: flex; flex-direction: column; gap: 2px;">
                        <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b;">Threat Source</span>
                        <span style="font-size: 12.5px; font-weight: 700; color: #0f172a;">User Prompt</span>
                    </div>

                    <!-- Cell 2: Attack Vector -->
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 10px; display: flex; flex-direction: column; gap: 2px;">
                        <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b;">Attack Vector</span>
                        <span id="pid-attack-type-text" style="font-size: 12.5px; font-weight: 700; color: #0f172a; word-break: break-word;"></span>
                    </div>

                    <!-- Cell 3: Risk -->
                    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 9px 10px; display: flex; flex-direction: column; gap: 2px;">
                        <span style="font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b;">Risk</span>
                        <div style="display: flex; align-items: baseline; justify-content: space-between; gap: 4px;">
                            <span style="font-size: 12.5px; font-weight: 800; color: #0f172a;"><span id="pid-risk-score-text"></span> / 100</span>
                            <span style="
                                background: ${badgeBg};
                                color: ${badgeColor};
                                border: 1px solid ${badgeBorder};
                                font-size: 9px;
                                font-weight: 700;
                                padding: 1px 5px;
                                border-radius: 9999px;
                                text-transform: uppercase;
                                letter-spacing: 0.03em;
                            "><span id="pid-risk-level-text"></span></span>
                        </div>
                        <div style="width: 100%; height: 5px; background: #e2e8f0; border-radius: 3px; overflow: hidden; margin-top: 3px;">
                            <div id="pid-risk-bar-fill" style="width: 0%; height: 100%; background: ${riskBarColor}; transition: width 0.4s ease;"></div>
                        </div>
                    </div>
                </div>

                <!-- Threat Evidence Section (if evidence is detected) -->
                <div id="pid-evidence-section" style="display: none; flex-direction: column; gap: 4px;">
                    <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;">Threat Evidence</span>
                    <div style="
                        background: #f8fafc;
                        border: 1px solid #e2e8f0;
                        border-left: 3px solid #ef4444;
                        border-radius: 6px;
                        padding: 8px 12px;
                        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
                        font-size: 12px;
                        color: #0f172a;
                        font-style: italic;
                        word-break: break-word;
                    "><span id="pid-evidence-text"></span></div>
                </div>

                <!-- Why It Was Blocked / Security Explanation -->
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    <span style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;">Why It Was Blocked</span>
                    <div id="pid-reason-text" style="
                        font-size: 12px;
                        color: ${reasonColor};
                        background: ${reasonBg};
                        border: 1px solid ${reasonBorder};
                        border-radius: 8px;
                        padding: 9px 12px;
                        line-height: 1.45;
                    "></div>
                </div>
            </div>

            <!-- Pinned Actions Footer -->
            <div style="
                flex-shrink: 0;
                padding: 12px 24px;
                border-top: 1px solid #e2e8f0;
                display: flex;
                justify-content: flex-end;
                align-items: center;
                gap: 10px;
                background: #ffffff;
            ">
                ${footerButtonsHtml}
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    // All backend-derived dynamic text is written via textContent, never
    // interpolated into the innerHTML template above — this is the only
    // place any of these values touch the DOM.
    const scannedEl = document.getElementById("pid-scanned-prompt-text");
    if (scannedEl) {
        scannedEl.textContent = promptText || "No prompt text captured.";
    }
    document.getElementById("pid-risk-level-text").textContent = layer1.risk_level || "UNKNOWN";
    const riskScoreValue = Number(layer1.risk_score) || 0;
    document.getElementById("pid-risk-score-text").textContent = String(riskScoreValue);
    document.getElementById("pid-risk-bar-fill").style.width = `${Math.min(100, Math.max(5, riskScoreValue))}%`;
    document.getElementById("pid-attack-type-text").textContent = layer1.attack_type || "Unknown";
    document.getElementById("pid-reason-text").textContent = layer1.reason || "No further explanation provided.";

    // Hydrate evidence section if available
    const evidenceEl = document.getElementById("pid-evidence-text");
    const evidenceSec = document.getElementById("pid-evidence-section");
    const rawEvidence = (backendData.threat_attribution && backendData.threat_attribution.prompt_evidence)
        || (layer1.matched_indicators && layer1.matched_indicators.length > 0 ? layer1.matched_indicators[0] : "");
    if (evidenceEl && evidenceSec) {
        if (rawEvidence && String(rawEvidence).trim().length > 0) {
            evidenceEl.textContent = String(rawEvidence).trim();
            evidenceSec.style.display = "flex";
        } else {
            evidenceSec.style.display = "none";
        }
    }

    const dismissHandler = () => {
        overlay.remove();
        if (onDismiss) onDismiss();
    };

    const dismissBtn = document.getElementById("pid-btn-dismiss");
    if (dismissBtn) {
        dismissBtn.addEventListener("click", dismissHandler);
    }

    const closeBtn = document.getElementById("pid-btn-close");
    if (closeBtn) {
        closeBtn.addEventListener("click", dismissHandler);
    }

    const proceedBtn = document.getElementById("pid-btn-proceed");
    if (proceedBtn) {
        proceedBtn.addEventListener("click", () => {
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

const SEND_BUTTON_SELECTORS = [
    'button[data-testid="send-button"]',
    'button[data-testid="fruitjuice-send-button"]',
    'button[data-testid*="send" i]',
    'button[aria-label*="send prompt" i]',
    'button[aria-label*="send message" i]',
    'button[aria-label*="send" i]',
    'button[aria-label*="submit" i]',
    'button#send-button',
    '#send-message-button',
    'form button[type="submit"]',
    'button.send-button',
    '[role="button"][data-testid*="send" i]',
    '[role="button"][aria-label*="send" i]'
];

function findSubmitButton(target) {
    if (!target) return null;
    const el = target.nodeType === 3 ? target.parentElement : target;
    if (!el || typeof el.closest !== "function") return null;

    for (const selector of SEND_BUTTON_SELECTORS) {
        try {
            const btn = el.closest(selector);
            if (btn) return btn;
        } catch (_) {}
    }
    const anyBtn = el.closest('button, [role="button"]');
    if (anyBtn) {
        const aria = (anyBtn.getAttribute("aria-label") || "").toLowerCase();
        const title = (anyBtn.getAttribute("title") || "").toLowerCase();
        const testid = (anyBtn.getAttribute("data-testid") || "").toLowerCase();
        const id = (anyBtn.id || "").toLowerCase();
        if (aria.includes("send") || aria.includes("submit") || aria.includes("prompt") ||
            title.includes("send") || title.includes("submit") ||
            testid.includes("send") || testid.includes("submit") ||
            id.includes("send") || id.includes("submit")) {
            return anyBtn;
        }
    }
    return null;
}

/**
 * Triggers prompt submission after inspection passes, replaying it the same
 * way it was originally triggered (Enter key vs. a send button click).
 */
function triggerOriginalSubmit() {
    // 1. If originally keydown, re-dispatch Enter with full standard keyboard properties
    if (lastInterceptionContext && lastInterceptionContext.type === "keydown" && lastInterceptionContext.element) {
        const targetEl = document.contains(lastInterceptionContext.element)
            ? lastInterceptionContext.element
            : (document.querySelector('#prompt-textarea, [contenteditable="true"], textarea') || document.activeElement);
        if (targetEl) {
            const enterDown = new KeyboardEvent("keydown", {
                key: "Enter",
                code: "Enter",
                keyCode: 13,
                which: 13,
                bubbles: true,
                cancelable: true
            });
            targetEl.dispatchEvent(enterDown);
            return;
        }
    }

    // 2. If originally click on button, re-trigger click on the exact button
    if (lastInterceptionContext && lastInterceptionContext.type === "click" && lastInterceptionContext.element) {
        if (document.contains(lastInterceptionContext.element)) {
            lastInterceptionContext.element.click();
            return;
        }
    }

    // 3. Fallback: Look for standard submit button or trigger form submit
    for (const selector of SEND_BUTTON_SELECTORS) {
        try {
            const btn = document.querySelector(selector);
            if (btn) {
                btn.click();
                return;
            }
        } catch (_) {}
    }

    const form = document.querySelector('form:has(#prompt-textarea), form:has(textarea)');
    if (form && typeof form.requestSubmit === "function") {
        form.requestSubmit();
    }
}

function approveAndResubmit() {
    isSubmissionApproved = true;
    lastKnownPromptText = "";
    triggerOriginalSubmit();
    // Safety auto-reset: ensures isSubmissionApproved cannot stay stuck as true
    setTimeout(() => {
        isSubmissionApproved = false;
    }, 600);
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

    if (isCheckingPrompt) {
        // Prevent duplicate concurrent requests while a check is in flight
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        return;
    }

    const currentText = getPromptText();
    const promptText = (currentText && currentText.trim().length > 0)
        ? currentText.trim()
        : (lastKnownPromptText ? lastKnownPromptText.trim() : "");

    if (!promptText || promptText.length < 2) return;

    // Prevent the default action FIRST, synchronously, before any await.
    e.preventDefault();
    e.stopPropagation();
    e.stopImmediatePropagation();

    isCheckingPrompt = true;
    lastInterceptionContext = { type: e.type, element: e.target };

    // Delegates to the background service worker, which calls the real
    // backend /secure-prompt pipeline. No security decision is made here.
    chrome.runtime.sendMessage({
        type: "CHECK_PROMPT",
        prompt: promptText
    }, (response) => {
        isCheckingPrompt = false;
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
                isCheckingPrompt = false;
            }, promptText);
        } else {
            showSafeToast(layer1.risk_score);
            approveAndResubmit();
        }
    });
}

// 1. Intercept Enter Key in inputs
document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && !e.ctrlKey && !e.altKey && !e.isComposing) {
        const active = document.activeElement;
        if (isPromptInputElement(active) || isPromptInputElement(e.target)) {
            handlePromptInterception(e);
        }
    }
}, true); // Use capture phase

// 2. Intercept Click on Submit Buttons
document.addEventListener("click", (e) => {
    const target = e.target;
    const button = findSubmitButton(target);
    if (button) {
        handlePromptInterception(e);
    }
}, true);

// 3. Intercept Form Submission (e.g. accessibility, programmatic, or Enter in form)
document.addEventListener("submit", (e) => {
    handlePromptInterception(e);
}, true);

// 4. Continuously track prompt text as user types and clicks so it is never lost on blur/clear
function trackPromptInput(e) {
    const text = getPromptText();
    if (text && text.trim().length > 0) {
        lastKnownPromptText = text.trim();
    }
}

document.addEventListener("input", trackPromptInput, true);
document.addEventListener("keyup", trackPromptInput, true);
document.addEventListener("change", trackPromptInput, true);
document.addEventListener("paste", trackPromptInput, true);
document.addEventListener("pointerdown", trackPromptInput, true);
document.addEventListener("mousedown", trackPromptInput, true);

// 5. Respond to Popup queries
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "GET_CURRENT_PROMPT") {
        const text = getPromptText();
        sendResponse({ text: text });
    }
});