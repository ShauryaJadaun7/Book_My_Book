from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from ..extensions import db, mail
from ..models import User
import random
import string
import redis
from flask import current_app
try:
    from twilio.rest import Client
except ImportError:
    pass

# Fallback dictionary for local dev without Redis
_fallback_otp_store = {}

def get_redis_client():
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/1')
    return redis.from_url(redis_url)

def generate_and_send_otp(email, phone=None):
    redis_client = get_redis_client()
    rate_limit_key = f"rate_limit:otp:{email}"
    otp_key = f"otp:{email}"
    otp_code = ''.join(random.choices(string.digits, k=6))
    otp_hash = generate_password_hash(otp_code)
    
    try:
        # Rate limiting: max 3 OTP requests per hour using Redis
        request_count = redis_client.incr(rate_limit_key)
        
        if request_count == 1:
            # Set expiry for 1 hour on first request
            redis_client.expire(rate_limit_key, 3600)
        
        if request_count > 3:
            return False, "Too many OTP requests. Please try again later."

        # Store hashed OTP for security in Redis with 10-minute expiry
        redis_client.setex(otp_key, 600, otp_hash)
    except redis.exceptions.ConnectionError:
        print(f"WARNING: Redis not available. Falling back to in-memory OTP store for {email}")
        now = datetime.now()
        
        if email not in _fallback_otp_store:
            _fallback_otp_store[email] = {'count': 0, 'first_req': now, 'otp_hash': None}
            
        store = _fallback_otp_store[email]
        first_req = store.get('first_req', now)
        
        # Reset count if older than 1 hour
        if isinstance(first_req, datetime) and now - first_req > timedelta(hours=1):
            store['count'] = 0
            store['first_req'] = now
            
        current_count = store.get('count', 0)
        if isinstance(current_count, int):
            store['count'] = current_count + 1
            if store['count'] > 3:
                return False, "Too many OTP requests. Please try again later."
                
        store['otp_hash'] = otp_hash
    
    # Send SMS (No longer sending OTP to email)
    if phone:
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        twilio_phone = current_app.config.get('TWILIO_PHONE_NUMBER')
        
        if account_sid and auth_token and twilio_phone:
            try:
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                    body=f"Your BookMyBook OTP is: {otp_code}. Do not share this code with anyone.",
                    from_=twilio_phone,
                    to=phone
                )
                print(f"Success! SMS sent. Message SID: {message.sid}")
            except Exception as e:
                print(f"Failed to send SMS via Twilio: {e}")
                return False, "Failed to send OTP SMS."
        else:
            print(f"\n[{datetime.now()}] DUMMY SMS SENDER")
            print(f"To: {phone}")
            print(f"Message: Your BookMyBook OTP is {otp_code}. Do not share this code with anyone.")
            print("-" * 30 + "\n")
        
    return True, "OTP sent successfully to phone."

def verify_otp(email, code):
    redis_client = get_redis_client()
    otp_key = f"otp:{email}"
    
    try:
        otp_hash_bytes = redis_client.get(otp_key)
        if not otp_hash_bytes:
            return False, "OTP not found, expired, or already used."
        otp_hash_str = otp_hash_bytes.decode('utf-8')
        used_redis = True
    except redis.exceptions.ConnectionError:
        print(f"WARNING: Redis not available. Verifying from in-memory OTP store for {email}")
        store = _fallback_otp_store.get(email)
        if not store or 'otp_hash' not in store:
            return False, "OTP not found, expired, or already used."
        otp_hash_str = store['otp_hash']
        used_redis = False
        
    if not check_password_hash(otp_hash_str, code):
        return False, "Invalid OTP."
        
    # Mark as used by deleting the key
    if used_redis:
        try:
            redis_client.delete(otp_key)
        except redis.exceptions.ConnectionError:
            pass
    else:
        _fallback_otp_store[email].pop('otp_hash', None)
        
    return True, "Valid"

def create_user_after_password(email, phone, full_name, password):
    user = User.query.filter_by(email=email).first()
    if user:
        return False, "User already exists."
        
    new_user = User(
        email=email, 
        phone=phone,
        full_name=full_name, 
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()
    return True, new_user

def update_user_password(user, old_password, new_password):
    if not check_password_hash(user.password_hash, old_password):
        return False, "Incorrect old password."
        
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return True, "Success"

def generate_random_password(length=10):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def send_password_email(email, password):
    msg = Message("Welcome to BookMyBook - Your Login Credentials", recipients=[email])
    msg.body = f"Hello,\n\nYour account has been successfully verified!\n\nYour system generated password is: {password}\n\nPlease use this password to log in next time. You can change it in your profile settings.\n\nBest,\nThe BookMyBook Team"
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")
        print(f"\n[{datetime.now()}] DUMMY EMAIL SENDER")
        print(f"To: {email}")
        print(f"Message: Your BookMyBook generated password is {password}. Do not share this code with anyone.")
        print("-" * 30 + "\n")
