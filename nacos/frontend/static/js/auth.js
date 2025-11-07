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

    // Function to show error with close icon and timeout
    function showError(errorDiv, message) {
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="error-close" style="position: absolute; right: 10px; top: 10px; background: none; border: none; color: red; font-size: 16px; cursor: pointer;">&times;</button>
        `;
        errorDiv.style.display = 'block';
        const closeButton = errorDiv.querySelector('.error-close');
        closeButton.addEventListener('click', () => {
            errorDiv.style.display = 'none';
            errorDiv.innerHTML = '';
        });
        setTimeout(() => {
            errorDiv.style.display = 'none';
            errorDiv.innerHTML = '';
        }, 30000);
    }

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
                    showError(errorDiv, data.message);
                }
            })
            .catch(error => {
                console.error('Login error:', error);
                isSubmitting = false;
                const errorDiv = document.querySelector('.login-error');
                showError(errorDiv, 'Either your Password or ID input does not match.');
            });
        });
    } else {
        console.log("Login form not found");
    }

  
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
                    window.location.replace(data.redirect_url || '/login/');
                } else {
                    const errorDiv = document.querySelector('.set-password-error');
                    showError(errorDiv, data.message);
                }
            })
            .catch(error => {
                console.error('Set-password error:', error);
                isSubmitting = false;
                const errorDiv = document.querySelector('.set-password-error');
                showError(errorDiv, 'An error in seeting your password occured');
            });
        });
    } else {
        console.log("Set-password form not found");
    }
});