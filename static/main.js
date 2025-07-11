document.addEventListener('DOMContentLoaded', () => {

    // --- Helper for Displaying Messages ---
    const showMessage = (message, category = 'success') => {
        const messageContainer = document.createElement('div');
        messageContainer.className = `notification ${category}`;
        messageContainer.textContent = message;

        document.body.appendChild(messageContainer);

        setTimeout(() => {
            messageContainer.remove();
        }, 3000);
    };

    // --- Add styles for notifications dynamically ---
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: #161b22;
            color: #c9d1d9;
            padding: 10px 20px;
            border-radius: 6px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            font-size: 14px;
        }
        .notification.success {
            border-left: 4px solid #238636;
        }
        .notification.error {
            border-left: 4px solid #f85149;
        }
    `;
    document.head.appendChild(style);

    // --- Sign Up Form ---
    const signupForm = document.querySelector('#signup-form');
    if (signupForm instanceof HTMLFormElement) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(signupForm);
            const data = Object.fromEntries(formData.entries());

            const response = await fetch('/api/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            const result = await response.json();
            if (result.success) {
                showMessage(result.message);
                window.location.href = '/signin';
            } else {
                showMessage(result.error, 'error');
            }
        });
    }

    // --- Sign In Form ---
    const signinForm = document.querySelector('#signin-form');
    if (signinForm instanceof HTMLFormElement) {
        signinForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(signinForm);
            const data = Object.fromEntries(formData.entries());

            const response = await fetch('/api/signin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            });

            const result = await response.json();
            if (result.success) {
                showMessage(result.message);
                window.location.href = '/profile';
            } else {
                showMessage(result.error, 'error');
            }
        });
    }

    // --- Profile Page Logic ---
    if (window.location.pathname === '/profile') {
        const usernameSpan = document.querySelector('#username');

        // Fetch profile data on page load
        (async () => {
            const response = await fetch('/api/profile');
            const result = await response.json();

            if (result.success && usernameSpan) {
                usernameSpan.textContent = result.username;
            } else {
                // If fetching profile fails, redirect to signin
                showMessage('Authentication failed. Please sign in.', 'error');
                window.location.href = '/signin';
            }
        })();

        // Handle file upload
        const uploadForm = document.querySelector('#upload-form');
        if (uploadForm instanceof HTMLFormElement) {
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(uploadForm);

                // Show loading spinner
                const submitButton = uploadForm.querySelector('button[type="submit"]');
                if (submitButton instanceof HTMLButtonElement) {
                    submitButton.disabled = true;
                    submitButton.textContent = 'Uploading...';
                }

                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData, // No 'Content-Type' header needed for FormData
                });

                const result = await response.json();
                if (result.success) {
                    showMessage(result.message);
                } else {
                    showMessage(result.error, 'error');
                }

                // Reset form and button state
                uploadForm.reset();
                if (submitButton instanceof HTMLButtonElement) {
                    submitButton.disabled = false;
                    submitButton.textContent = 'Upload Repository';
                }
            });
        }
    }

    // --- Logout Logic ---
    const logoutLinks = document.querySelectorAll('a[href="/logout"]');
    logoutLinks.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const response = await fetch('/api/logout', { method: 'POST' });
            const result = await response.json();

            if (result.success) {
                showMessage(result.message);
                window.location.href = '/';
            } else {
                showMessage(result.error, 'error');
            }
        });
    });
});