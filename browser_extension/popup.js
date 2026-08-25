document.addEventListener("DOMContentLoaded", () => {

    const scanBtn = document.getElementById("scanBtn");
    const scanResult = document.getElementById("scanResult");

    scanBtn.addEventListener("click", () => {

        chrome.runtime.sendMessage(
            {
                type: "SCAN_CURRENT_TAB"
            },
            (response) => {

                const text = response?.text?.trim();

                if (text) {

                    scanResult.textContent =
                        text.length > 150
                            ? text.substring(0, 150) + "..."
                            : text;

                } else {

                    scanResult.textContent =
                        "No prompt found in the input box.";

                }

            }
        );

    });

});

console.log("Prompt Injection Detector: popup loaded");