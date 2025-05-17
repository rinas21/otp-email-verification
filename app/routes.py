from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.utils.otp_utils import (
    generate_otp, save_otp_data, is_otp_expired,
    is_on_cooldown, verify_otp, clear_otp_data
)
from app.services.email_service import send_otp_email
from app.config import Config

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Email input page"""
    if request.method == 'POST':
        email = request.form['email']
        
        # Check cooldown
        on_cooldown, remaining = is_on_cooldown(email,Config.OTP_RESEND_COOLDOWN)
        if on_cooldown:
            flash(f"Please wait {remaining} seconds before requesting a new OTP.", "warning")
            return render_template('index.html')
        
        # Generate and send OTP
        otp = generate_otp()
        success, message = send_otp_email(email, otp)
        
        if success:
            save_otp_data(otp, email)
            flash("OTP sent successfully! Please check your email.", "success")
            return redirect(url_for('main.verify'))
        else:
            flash(message, "danger")
    
    return render_template('index.html')

@main_bp.route('/verify', methods=['GET', 'POST'])
def verify():
    """OTP verification page"""
    # Check if OTP exists and is not expired
    if 'otp' not in session or is_otp_expired(Config.OTP_EXPIRY):
        flash("OTP expired or not generated. Please request a new OTP.", "warning")
        return redirect(url_for('main.index'))
    
    # Get cooldown info for resend button
    email = session.get('email', '')
    on_cooldown, cooldown_remaining = is_on_cooldown(email,Config.OTP_RESEND_COOLDOWN)
    
    if request.method == 'POST':
        # Get OTP from form
        user_otp = ''.join([request.form.get(f'otp_{i}', '') for i in range(6)])
        
        # Verify OTP
        success, message, attempts = verify_otp(user_otp)
        
        if success:
            clear_otp_data()
            flash(message, "success")
            return render_template('success.html')
        else:
            flash(message, "danger")
            
            # If too many attempts, redirect to start
            if attempts >= 3:
                clear_otp_data()
                flash("Too many wrong attempts. Please request a new OTP.", "warning")
                return redirect(url_for('main.index'))
    
    email = session.get('email', '')
    masked_email = email[:3] + '*' * (len(email.split('@')[0]) - 3) + '@' + email.split('@')[1]
    
    return render_template('verify.html', 
                          cooldown_remaining=cooldown_remaining,
                          on_cooldown=on_cooldown,
                          masked_email=masked_email)

@main_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP"""
    # Check cooldown
    email = session.get('email', '')
    on_cooldown, _ = is_on_cooldown(email,Config.OTP_RESEND_COOLDOWN)
    if on_cooldown:
        flash("Please wait before requesting a new OTP.", "warning")
        return redirect(url_for('main.verify'))
    
    # Get email from session
    email = session.get('email')
    if not email:
        flash("Email not found. Please try again.", "danger")
        return redirect(url_for('main.index'))
    
    # Generate and send new OTP
    otp = generate_otp()
    success, message = send_otp_email(email, otp)
    
    if success:
        save_otp_data(otp, email)
        flash("New OTP sent successfully! Please check your email.", "success")
    else:
        flash(message, "danger")
    
    return redirect(url_for('main.verify'))