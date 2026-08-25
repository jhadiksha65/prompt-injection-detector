// Content script - prompt interception logic will be added in later steps
console.log("Prompt Injection Detector: content script loaded");// Function to capture the current prompt text
function getPromptText() {

    // For Gemini, ChatGPT, Claude (contenteditable input)
    let el = document.querySelector('div[contenteditable="true"]');

    if (el) {
        return el.innerText || el.textContent || "";
    }

    // Fallback for websites using textarea
    el = document.querySelector("textarea");

    if (el) {
        return el.value || "";
    }

    return "";
}

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

    if (message.type === "GET_CURRENT_PROMPT") {

        const text = getPromptText();

        console.log("Captured Prompt:", text);

        sendResponse({
            text: text
        });
    }
});

console.log("Prompt Injection Detector: content script loaded");