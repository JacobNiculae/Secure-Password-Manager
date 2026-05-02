chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "generate_password") {
        fetch("http://127.0.0.1:5000/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                site: message.site,
                username: message.username || ""
            })
        })
        .then(res => res.json())
        .then(data => sendResponse({ success: true, password: data.password }))
        .catch(err => sendResponse({ success: false, error: err.message }));
        return true;
    }
});