document.addEventListener('DOMContentLoaded', () => {
    // Get all form elements
    const form = document.getElementById('signup-form');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const sendOtpBtn = document.getElementById('send-otp-btn');
    const verifyOtpBtn = document.getElementById('verify-otp-btn');
    const resendOtpBtn = document.getElementById('resend-otp-btn');
    const otpSection = document.getElementById('otp-section');
    const otpInput = document.getElementById('otp');
    const signupBtn = document.getElementById('signup-btn');

    // Get all error/success message elements
    const emailError = document.getElementById('email-error');
    const passwordError = document.getElementById('password-error');
    const confirmPasswordError = document.getElementById('confirm-password-error');
    const otpError = document.getElementById('otp-error');

    let timer;
    let timeLeft = 300; // 5 minutes

    // Password strength checker
    passwordInput.addEventListener('input', function() {
        const password = this.value;
        const strength = checkPasswordStrength(password);
        const strengthDiv = document.getElementById('password-strength');
        
        strengthDiv.className = 'password-strength ' + strength.class;
        strengthDiv.textContent = strength.message;

        // Also check confirm password match if it has a value
        if (confirmPasswordInput.value) {
            validatePasswordMatch();
        }
    });

    // Confirm password matcher
    confirmPasswordInput.addEventListener('input', validatePasswordMatch);

    function validatePasswordMatch() {
        if (passwordInput.value !== confirmPasswordInput.value) {
            showError(confirmPasswordError, 'Passwords do not match');
            return false;
        }
        confirmPasswordError.textContent = '';
        return true;
    }

    // Send OTP button handler
    sendOtpBtn.addEventListener('click', async () => {
        // Clear previous messages
        clearMessages();

        // Validate form before sending OTP
        if (!validateForm()) return;

       try {
    const response = await fetch('http://localhost:5501/api/send-otp', {  // Changed from /api/signup
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email })
    });

            const data = await response.json();

            if (data.success) {
                otpSection.style.display = 'block';
                showSuccess(emailError, 'OTP sent successfully!');
                startTimer();
                resendOtpBtn.style.display = 'none';
                
                // Store credentials temporarily
                window.tempEmail = emailInput.value.trim();
                window.tempPassword = passwordInput.value;
                
                // Disable inputs after OTP is sent
                emailInput.disabled = true;
                passwordInput.disabled = true;
                confirmPasswordInput.disabled = true;
                sendOtpBtn.disabled = true;
            } else {
                showError(emailError, data.message || 'Failed to send OTP');
            }
        } catch (error) {
            showError(emailError, 'Failed to connect to server');
        }
    });

    // Verify OTP button handler
    verifyOtpBtn.addEventListener('click', async () => {
        const otp = otpInput.value.trim();
        
        if (!otp) {
            showError(otpError, 'Please enter OTP');
            return;
        }

        try {
            const response = await fetch(`${API_URL}/api/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    email: window.tempEmail, 
                    otp: otp 
                })
            });

            const data = await response.json();

            if (data.success) {
                showSuccess(otpError, 'OTP verified successfully! Creating account...');
                clearInterval(timer);
                
                // Proceed with signup
                const signupResponse = await fetch(`${API_URL}/api/signup`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: window.tempEmail,
                        password: window.tempPassword
                    })
                });

                const signupData = await signupResponse.json();
                if (signupData.success) {
                    showSuccess(otpError, 'Account created! Redirecting to login...');
                    
                    // Clear sensitive data
                    window.tempEmail = null;
                    window.tempPassword = null;
                    
                    // Redirect to login page
                    setTimeout(() => {
                        window.location.href = '/login.html';
                    }, 1500);
                } else {
                    showError(otpError, signupData.message || 'Failed to create account');
                }
            } else {
                showError(otpError, data.message || 'Invalid OTP');
            }
        } catch (error) {
            showError(otpError, 'Failed to connect to server');
        }
    });

    // Resend OTP button handler
    resendOtpBtn.addEventListener('click', async () => {
        resendOtpBtn.style.display = 'none';
        await sendOtpBtn.click();
    });

    // Helper Functions
    function validateForm() {
        let isValid = true;

        // Validate email
        if (!emailInput.value.trim()) {
            showError(emailError, 'Email is required');
            isValid = false;
        } else if (!validateEmail(emailInput.value.trim())) {
            showError(emailError, 'Please enter a valid email address');
            isValid = false;
        }

        // Validate password
        if (!passwordInput.value) {
            showError(passwordError, 'Password is required');
            isValid = false;
        } else {
            const strength = checkPasswordStrength(passwordInput.value);
            if (strength.class === 'weak') {
                showError(passwordError, 'Password is too weak');
                isValid = false;
            }
        }

        // Validate password match
        if (!validatePasswordMatch()) {
            isValid = false;
        }

        return isValid;
    }

    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function checkPasswordStrength(password) {
        if (password.length === 0) return { message: '', class: '' };
        
        const hasLower = /[a-z]/.test(password);
        const hasUpper = /[A-Z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecial = /[!@#$%^&*]/.test(password);
        
        const strength = hasLower + hasUpper + hasNumber + hasSpecial;

        if (password.length >= 8 && strength >= 3) {
            return { message: 'Strong', class: 'strong' };
        } else if (password.length >= 6 && strength >= 2) {
            return { message: 'Medium', class: 'medium' };
        } else {
            return { message: 'Weak', class: 'weak' };
        }
    }

    function showError(element, message) {
        element.textContent = message;
        element.className = 'error-message';
    }

    function showSuccess(element, message) {
        element.textContent = message;
        element.className = 'success-message';
    }

    function clearMessages() {
        emailError.textContent = '';
        passwordError.textContent = '';
        confirmPasswordError.textContent = '';
        otpError.textContent = '';
    }

    function startTimer() {
        clearInterval(timer);
        timeLeft = 300;
        updateTimerDisplay();
        
        timer = setInterval(() => {
            timeLeft--;
            updateTimerDisplay();
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                resendOtpBtn.style.display = 'block';
                document.getElementById('timer').textContent = 'OTP expired';
            }
        }, 1000);
    }

    function updateTimerDisplay() {
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        document.getElementById('timer').textContent = 
            `Time remaining: ${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
});
// Update API_URL to point to your Flask backend
const API_URL = 'http://localhost:5000';  // Backend URL

sendOtpBtn.addEventListener('click', async () => {
    clearMessages();
    if (!validateForm()) return;

    try {
        // First verify OTP
        const verifyResponse = await fetch(`${API_URL}/verify-otp`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: emailInput.value.trim(),
                otp: otpInput.value.trim()
            })
        });

        const verifyData = await verifyResponse.json();

        if (verifyResponse.ok) {
            // If OTP is verified, proceed with signup
            const signupResponse = await fetch(`${API_URL}/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: emailInput.value.trim(),
                    password: passwordInput.value
                })
            });

            const signupData = await signupResponse.json();

            if (signupResponse.ok) {
                showSuccess(otpError, 'Account created successfully! Redirecting to login...');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 2000);
            } else {
                showError(otpError, signupData.error || 'Failed to create account');
            }
        } else {
            showError(otpError, verifyData.error || 'Invalid OTP');
        }
    } catch (error) {
        showError(otpError, 'Failed to connect to server');
        console.error('Error:', error);
    }
});
// Update the form submit handler
form.addEventListener('submit', (e) => {
    e.preventDefault(); // Prevent form submission
    });