function isSignupForm() {
    const inputs = document.querySelectorAll('input');
    let hasPassword = false;

    inputs.forEach(input => {
        if (input.type === 'password') hasPassword = true;
    });

    return hasPassword;
}

function getPasswordField() {
    return document.querySelector('input[type="password"]');
}

function showPrompt(passwordField) {
    if (document.getElementById('spm-prompt')) return;

    const prompt = document.createElement('div');
    prompt.id = 'spm-prompt';
    prompt.style.cssText = `
        position: fixed;
        bottom: 24px;
        right: 24px;
        background: #1e1e2e;
        border: 1px solid #7c6af7;
        border-radius: 12px;
        padding: 16px 20px;
        z-index: 999999;
        font-family: 'Segoe UI', sans-serif;
        color: #cdd6f4;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        display: flex;
        flex-direction: column;
        gap: 10px;
        min-width: 260px;
    `;

    prompt.innerHTML = `
        <div style="font-size: 14px; font-weight: bold; color: #cdd6f4;">
            🔐 Secure Password Manager
        </div>
        <div style="font-size: 12px; color: #a6adc8;">
            Password field detected. Generate a secure password?
        </div>
        <div style="display: flex; gap: 8px;">
            <button id="spm-generate" style="
                flex: 1;
                background: #7c6af7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
            ">Generate</button>
            <button id="spm-dismiss" style="
                flex: 1;
                background: #2a2a3d;
                color: #a6adc8;
                border: 1px solid #444466;
                border-radius: 6px;
                padding: 8px;
                cursor: pointer;
                font-size: 12px;
            ">Dismiss</button>
        </div>
    `;

    document.body.appendChild(prompt);

    document.getElementById('spm-generate').addEventListener('click', () => {
        const site = window.location.hostname;
        chrome.runtime.sendMessage(
            { action: "generate_password", site: site },
            (response) => {
                if (response?.success) {
                    passwordField.value = response.password;
                    passwordField.dispatchEvent(new Event('input', { bubbles: true }));
                    prompt.innerHTML = `
                        <div style="font-size: 13px; color: #a6e3a1;">
                            ✅ Password generated and saved to vault!
                        </div>
                    `;
                    setTimeout(() => prompt.remove(), 3000);
                } else {
                    prompt.innerHTML = `
                        <div style="font-size: 13px; color: #f38ba8;">
                            ❌ Could not connect to vault. Is the app running?
                        </div>
                    `;
                    setTimeout(() => prompt.remove(), 3000);
                }
            }
        );
    });

    document.getElementById('spm-dismiss').addEventListener('click', () => {
        prompt.remove();
    });
}

function checkForSignupForm() {
    if (isSignupForm()) {
        const passwordField = getPasswordField();
        if (passwordField) {
            showPrompt(passwordField);
        }
    }
}

setTimeout(checkForSignupForm, 1500);
setTimeout(checkForSignupForm, 3000);
setTimeout(checkForSignupForm, 5000);

const observer = new MutationObserver(() => {
    if (!document.getElementById('spm-prompt')) {
        checkForSignupForm();
    }
});

observer.observe(document.body, { childList: true, subtree: true });