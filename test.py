from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
import bcrypt
import random
import datetime
from twilio.rest import Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')

# Twilio Configuration

app.config['TWILIO_ACCOUNT_SID'] = ''  # Your Twilio Account SID
app.config['TWILIO_AUTH_TOKEN'] = ''    # Your Twilio Auth Token
app.config['TWILIO_PHONE_NUMBER'] = ''  # Your Twilio phone number


db = SQLAlchemy(app)
jwt = JWTManager(app)

# Model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aadhaar = db.Column(db.String(12), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))
    country = db.Column(db.String(100))
    password = db.Column(db.String(128), nullable=False)
    aadhaar_otp = db.Column(db.String(6))
    otp_expiry = db.Column(db.DateTime)

with app.app_context():
    db.create_all()

def format_phone_number(phone_number):
    """Format phone number to E.164 format"""
    phone_number = ''.join(filter(str.isdigit, phone_number))
    if not phone_number.startswith('+'):
        # Assuming Indian numbers, add +91 prefix if not present
        if phone_number.startswith('91'):
            phone_number = '+' + phone_number
        else:
            phone_number = '+91' + phone_number.lstrip('0')
    return phone_number

def send_otp_phone(phone_number, otp):
    """Send OTP via Twilio SMS"""
    try:
        # Format phone number
        formatted_phone = format_phone_number(phone_number)
        
        # Initialize Twilio client
        client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
        
        # Send message
        message = client.messages.create(
            body=f"Your verification OTP is: {otp}. Valid for 5 minutes.",
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=formatted_phone
        )
        
        print(f"Message SID: {message.sid}")
        return True
    except Exception as e:
        print(f"Twilio Error: {str(e)}")
        return False

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Extract data from request
        aadhaar = data.get('aadhaar')
        full_name = data.get('full_name')
        email = data.get('email')
        phone = data.get('phone')
        address = data.get('address')
        country = data.get('country')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        aadhaar_otp = data.get('aadhaar_otp')

        # Validate required fields
        if not all([aadhaar, full_name, email, phone, password, confirm_password, aadhaar_otp]):
            return jsonify({"message": "All fields are required"}), 400

        # Check password confirmation
        if password != confirm_password:
            return jsonify({"message": "Passwords do not match"}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Verify OTP
        user = User.query.filter_by(aadhaar=aadhaar).first()
        if not user or user.aadhaar_otp != aadhaar_otp or user.otp_expiry < datetime.datetime.now():
            return jsonify({"message": "Invalid or expired OTP"}), 400

        # Create new user
        new_user = User(
            aadhaar=aadhaar,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            country=country,
            password=hashed_password,
            aadhaar_otp=None,
            otp_expiry=None
        )

        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "Account created successfully"}), 201

    except Exception as e:
        print(f"Signup Error: {str(e)}")
        return jsonify({"message": "An error occurred during signup"}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({"message": "Invalid credentials"}), 401

        access_token = create_access_token(identity=user.id)
        return jsonify({
            "message": "Login successful",
            "token": access_token
        }), 200

    except Exception as e:
        print(f"Login Error: {str(e)}")
        return jsonify({"message": "An error occurred during login"}), 500

@app.route('/send-aadhaar-otp', methods=['POST'])
def send_aadhaar_otp():
    try:
        data = request.get_json()
        phone = data.get('phone')
        aadhaar = data.get('aadhaar')
        
        if not phone or not aadhaar:
            return jsonify({"message": "Phone number and Aadhaar are required"}), 400
        
        # Generate OTP
        otp = str(random.randint(100000, 999999))
        otp_expiry = datetime.datetime.now() + datetime.timedelta(minutes=5)
        
        # Save or update user
        user = User.query.filter_by(aadhaar=aadhaar).first()
        if user:
            user.aadhaar_otp = otp
            user.otp_expiry = otp_expiry
            user.phone = phone
        else:
            user = User(
                aadhaar=aadhaar,
                phone=phone,
                aadhaar_otp=otp,
                otp_expiry=otp_expiry
            )
            db.session.add(user)
        
        # Send OTP
        if send_otp_phone(phone, otp):
            db.session.commit()
            return jsonify({"message": "OTP sent successfully"}), 200
        else:
            return jsonify({"message": "Failed to send OTP"}), 500

    except Exception as e:
        print(f"Send OTP Error: {str(e)}")
        return jsonify({"message": "An error occurred while sending OTP"}), 500

@app.route('/test-sms', methods=['POST'])
def test_sms():
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        if not phone:
            return jsonify({"message": "Phone number is required"}), 400
        
        formatted_phone = format_phone_number(phone)
        
        client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
        message = client.messages.create(
            body="Test message from your application",
            from_=app.config['TWILIO_PHONE_NUMBER'],
            to=formatted_phone
        )
        
        return jsonify({
            "message": "Test SMS sent successfully",
            "sid": message.sid,
            "status": message.status
        }), 200
        
    except Exception as e:
        print(f"Test SMS Error: {str(e)}")
        return jsonify({
            "message": "Failed to send test SMS",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)