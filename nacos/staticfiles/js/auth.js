document.addEventListener('DOMContentLoaded', function() {
    console.log("auth.js loaded successfully at", new Date().toISOString());

    let isSubmitting = false;

    // Check session state
    fetch('/check-session/', {
        method: 'GET',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.json())
    .then(data => console.log("Session state:", data))
    .catch(error => console.error("Session check error:", error));

    // Login form submission
    const loginForm = document.querySelector('.login-form');
    if (loginForm) {
        console.log("Login form found");
        loginForm.addEventListener('submit', function(event) {
            event.preventDefault();
            if (isSubmitting) {
                console.log("Submission blocked: already submitting");
                return;
            }
            isSubmitting = true;
            const formData = new FormData(loginForm);
            const csrfToken = document.querySelector('.csrf-token input[name="csrfmiddlewaretoken"]')?.value;
            console.log("Submitting login form with username:", formData.get('username'));
            fetch('/login/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                },
                body: formData
            })
            .then(response => {
                console.log("Login response status:", response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Login response data:", data);
                isSubmitting = false;
                if (data.success) {
                    loginForm.reset();
                    window.location.replace(data.redirect_url || '/login/');
                } else {
                    const errorDiv = document.querySelector('.login-error');
                    errorDiv.textContent = data.message || 'Invalid login credentials';
                    errorDiv.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                isSubmitting = false;
                const errorDiv = document.querySelector('.login-error');
                errorDiv.textContent = 'An error occurred. Please try again.';
                errorDiv.style.display = 'block';
            });
        });
    } else {
        console.log("Login form not found");
    }

    // Set-password form submission
    const setPasswordForm = document.querySelector('.set-password-form');
    if (setPasswordForm) {
        console.log("Set-password form found");
        setPasswordForm.addEventListener('submit', function(event) {
            event.preventDefault();
            if (isSubmitting) {
                console.log("Submission blocked: already submitting");
                return;
            }
            isSubmitting = true;
            const formData = new FormData(setPasswordForm);
            const csrfToken = document.querySelector('.csrf-token input[name="csrfmiddlewaretoken"]')?.value;
            console.log("Submitting set-password form");
            fetch('/set-password/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                    'Cache-Control': 'no-cache, no-store, must-revalidate'
                },
                body: formData
            })
            .then(response => {
                console.log("Set-password response status:", response.status);
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Set-password response data:", data);
                isSubmitting = false;
                if (data.success) {
                    setPasswordForm.reset();
                    alert(data.message || 'Password set successfully!');
                    window.location.replace(data.redirect_url || '/login/');
                } else {
                    const errorDiv = document.querySelector('.set-password-error');
                    errorDiv.textContent = data.message || 'Error setting password';
                    errorDiv.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Set-password error:', error);
                isSubmitting = false;
                const errorDiv = document.querySelector('.set-password-error');
                errorDiv.textContent = 'An error occurred. Please try again.';
                errorDiv.style.display = 'block';
            });
        });
    } else {
        console.log("Set-password form not found");
    }
});