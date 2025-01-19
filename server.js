require('dotenv').config();
const express = require('express');
const cors = require('cors');
const nodemailer = require('nodemailer');
const bodyParser = require('body-parser');

const app = express();

// Middleware
app.use(cors({
    origin: 'http://127.0.0.1:5501',  // Updated to match your exact frontend URL
    methods: ['GET', 'POST'],
    credentials: true
}));
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Store OTPs temporarily (in production, use a database)
const otpStore = new Map();

// Email transporter configuration
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: 'siddnautiyaal@gmail.com',
        pass: 'jijdcvkqevayevwf'
    }
});

// Generate OTP
function generateOTP() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// Validate email format
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Send OTP endpoint
app.post('/api/send-otp', async (req, res) => {
    try {
        const { email } = req.body;
        console.log('Received email:', email); // Debug log

        // Validate email
        if (!email || !isValidEmail(email)) {
            return res.status(400).json({
                success: false,
                message: 'Please provide a valid email address'
            });
        }

        // Generate OTP
        const otp = generateOTP();
        console.log('Generated OTP:', otp); // Debug log
        
        // Store OTP with timestamp
        otpStore.set(email, {
            otp: otp,
            timestamp: Date.now(),
            attempts: 0
        });

        // Email configuration
        const mailOptions = {
            from: 'siddnautiyaal@gmail.com',
            to: email,
            subject: 'Your OTP Verification Code',
            html: `
                <h1>Email Verification</h1>
                <p>Your OTP for verification is: <strong>${otp}</strong></p>
                <p>This OTP will expire in 5 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
            `
        };

        // Send email
        await transporter.sendMail(mailOptions);
        console.log('Email sent successfully'); // Debug log

        res.json({
            success: true,
            message: 'OTP sent successfully'
        });
    } catch (error) {
        console.error('Error sending OTP:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to send OTP'
        });
    }
});

// Verify OTP endpoint
app.post('/api/verify-otp', (req, res) => {
    try {
        const { email, otp } = req.body;

        // Check if email and OTP exist
        if (!email || !otp) {
            return res.status(400).json({
                success: false,
                message: 'Please provide both email and OTP'
            });
        }

        // Get stored OTP data
        const otpData = otpStore.get(email);

        // Check if OTP exists
        if (!otpData) {
            return res.status(400).json({
                success: false,
                message: 'No OTP found for this email. Please request a new OTP'
            });
        }

        // Check OTP expiration (5 minutes)
        if (Date.now() - otpData.timestamp > 5 * 60 * 1000) {
            otpStore.delete(email);
            return res.status(400).json({
                success: false,
                message: 'OTP has expired. Please request a new one'
            });
        }

        // Check attempts
        if (otpData.attempts >= 3) {
            otpStore.delete(email);
            return res.status(400).json({
                success: false,
                message: 'Too many failed attempts. Please request a new OTP'
            });
        }

        // Verify OTP
        if (otpData.otp === otp) {
            otpStore.delete(email);
            return res.json({
                success: true,
                message: 'OTP verified successfully'
            });
        } else {
            // Increment failed attempts
            otpData.attempts += 1;
            otpStore.set(email, otpData);
            
            return res.status(400).json({
                success: false,
                message: `Invalid OTP. ${3 - otpData.attempts} attempts remaining`
            });
        }

    } catch (error) {
        console.error('Error verifying OTP:', error);
        res.status(500).json({
            success: false,
            message: 'Error verifying OTP. Please try again later.'
        });
    }
});

// Cleanup expired OTPs periodically (every 15 minutes)
setInterval(() => {
    const now = Date.now();
    for (const [email, data] of otpStore.entries()) {
        if (now - data.timestamp > 15 * 60 * 1000) {
            otpStore.delete(email);
        }
    }
}, 15 * 60 * 1000);

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'Server is running' });
});

// Test endpoint
app.get('/test', (req, res) => {
    res.json({ message: 'Server is working!' });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({
        success: false,
        message: 'Something went wrong!'
    });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
    console.log('Email server configured and ready');
});