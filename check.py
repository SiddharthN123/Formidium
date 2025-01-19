from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import re
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://127.0.0.1:5501", "http://localhost:5501"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Store OTPs (in production, use a database)
otp_store = {}

# Get email configuration from environment variables
EMAIL_ADDRESS = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASS')

def generate_otp():
    return str(random.randint(100000, 999999))

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_email(to_email, otp):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = 'Your OTP Verification Code'

        body = f"""
        <h1>Email Verification</h1>
        <p>Your OTP for verification is: <strong>{otp}</strong></p>
        <p>This OTP will expire in 5 minutes.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        msg.attach(MIMEText(body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email or not is_valid_email(email):
            return jsonify({'error': 'Invalid email address'}), 400
        
        otp = generate_otp()
        if send_email(email, otp):
            otp_store[email] = {
                'otp': otp,
                'timestamp': time.time()
            }
            return jsonify({'message': 'OTP sent successfully'}), 200
        return jsonify({'error': 'Failed to send OTP'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        user_otp = data.get('otp')
        
        if not email or not user_otp:
            return jsonify({'error': 'Email and OTP are required'}), 400
            
        stored_data = otp_store.get(email)
        if not stored_data:
            return jsonify({'error': 'No OTP found for this email'}), 400
            
        if time.time() - stored_data['timestamp'] > 300:  # 5 minutes expiry
            del otp_store[email]
            return jsonify({'error': 'OTP has expired'}), 400
            
        if stored_data['otp'] != user_otp:
            return jsonify({'error': 'Invalid OTP'}), 400
            
        del otp_store[email]
        return jsonify({'message': 'OTP verified successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        print("Error: Email configuration missing. Check your .env file.")
        exit(1)
    
    print(f"Server starting with email: {EMAIL_ADDRESS}")
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Failed to start server: {e}")