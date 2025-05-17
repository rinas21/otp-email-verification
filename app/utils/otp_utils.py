import random
import time
from flask import session

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def save_otp_data(otp, email):
    """Save OTP data in session"""
    session['otp'] = otp
    session['email'] = email
    session['otp_sent_time'] = time.time()
    session['otp_attempts'] = 0
    # Track cooldown per email
    cooldown_info = session.get('otp_cooldown', {})
    cooldown_info[email] = time.time()
    session['otp_cooldown'] = cooldown_info

def is_otp_expired(expiry_seconds):
    """Check if OTP is expired"""
    otp_sent_time = session.get('otp_sent_time', 0)
    return time.time() - otp_sent_time > expiry_seconds

def is_on_cooldown(email, cooldown_seconds):
    """Check if a specific email is on cooldown"""
    cooldown_info = session.get('otp_cooldown', {})
    last_sent_time = cooldown_info.get(email, 0)
    cooldown_remaining = max(0, cooldown_seconds - (time.time() - last_sent_time))
    return cooldown_remaining > 0, int(cooldown_remaining)

def verify_otp(user_otp):
    """Verify the entered OTP"""
    stored_otp = session.get('otp')
    attempts = session.get('otp_attempts', 0)
    
    if not stored_otp:
        return False, "OTP not found. Please request a new OTP.", attempts
    
    if user_otp == stored_otp:
        return True, "OTP verified successfully!", attempts
    
    # Increment attempts
    attempts += 1
    session['otp_attempts'] = attempts
    
    return False, f"Invalid OTP. Attempts left: {3 - attempts}", attempts

def clear_otp_data():
    """Clear OTP related data from session"""
    session.pop('otp', None)
    session.pop('otp_sent_time', None)
    session.pop('otp_attempts', None)