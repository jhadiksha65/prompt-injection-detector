// Listen for popup requests
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {

    if (message.type === "SCAN_CURRENT_TAB") {

        chrome.tabs.query(
            {
                active: true,
                currentWindow: true
            },
            (tabs) => {

                const tabId = tabs[0]?.id;

                if (!tabId) {
                    sendResponse({
                        text: ""
                    });
                    return;
                }

                chrome.tabs.sendMessage(
                    tabId,
                    {
                        type: "GET_CURRENT_PROMPT"
                    },
                    (response) => {

                        if (chrome.runtime.lastError) {
                            console.error(chrome.runtime.lastError);

                            sendResponse({
                                text: ""
                            });

                            return;
                        }

                        sendResponse({
                            text: response?.text || ""
                        });
                    }
                );

            }
        );

        return true;
    }

});

console.log("Prompt Injection Detector: background script loaded");