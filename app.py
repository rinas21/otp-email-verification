from flask import Flask, request, session, redirect, url_for, render_template_string
import random
import smtplib
from email.mime.text import MIMEText
import time
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
app.secret_key = 'replace_this_with_a_secure_key'

SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

OTP_EXPIRY = 300  # seconds (5 minutes)
OTP_RESEND_COOLDOWN = 30  # seconds

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp(email, otp):
    body = f'Your OTP code is: {otp}'
    msg = MIMEText(body)
    msg['Subject'] = 'Your OTP Code'
    msg['From'] = SENDER_EMAIL
    msg['To'] = email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    now = time.time()
    if request.method == 'POST':
        email = request.form['email']
        last_sent = session.get('otp_sent_time', 0)
        if now - last_sent < OTP_RESEND_COOLDOWN:
            error = f"Please wait {int(OTP_RESEND_COOLDOWN - (now - last_sent))} seconds before requesting a new OTP."
        else:
            otp = generate_otp()
            session['otp'] = otp
            session['email'] = email
            session['otp_sent_time'] = now
            session['otp_attempts'] = 0
            send_otp(email, otp)
            return redirect(url_for('verify'))
    return render_template_string('''
        <h2>Enter your email to receive OTP</h2>
        {% if error %}
          <p style="color:red;">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <input type="email" name="email" required placeholder="Enter your email" />
            <input type="submit" value="Send OTP" />
        </form>
    ''', error=error)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    error = None
    success = None
    now = time.time()
    otp = session.get('otp')
    otp_sent_time = session.get('otp_sent_time', 0)
    attempts = session.get('otp_attempts', 0)
    if not otp or (now - otp_sent_time > OTP_EXPIRY):
        error = "OTP expired or not generated. Please request a new OTP."
        return redirect(url_for('index'))

    if request.method == 'POST':
        user_otp = request.form['otp']
        if user_otp == otp:
            success = "OTP Verified Successfully!"
            # Clear session OTP after success
            session.pop('otp', None)
            session.pop('otp_sent_time', None)
            session.pop('otp_attempts', None)
            return render_template_string('''
                <h3 style="color:green;">{{ success }}</h3>
                <a href="{{ url_for('index') }}">Go back</a>
            ''', success=success)
        else:
            attempts += 1
            session['otp_attempts'] = attempts
            if attempts >= 3:
                error = "Too many wrong attempts. Please request a new OTP."
                # Clear OTP to force new request
                session.pop('otp', None)
                session.pop('otp_sent_time', None)
                session.pop('otp_attempts', None)
                return redirect(url_for('index'))
            else:
                error = f"Invalid OTP. Attempts left: {3 - attempts}"

    # Calculate cooldown remaining for resend button
    cooldown_remaining = max(0, OTP_RESEND_COOLDOWN - (now - otp_sent_time))

    return render_template_string('''
        <h2>Enter OTP sent to {{ session['email'] }}</h2>
        {% if error %}
          <p style="color:red;">{{ error }}</p>
        {% endif %}
        <form method="POST">
            <input type="text" name="otp" required placeholder="Enter OTP" maxlength="6" />
            <input type="submit" value="Verify OTP" />
        </form>
        <br>
        {% if cooldown_remaining > 0 %}
          <p>Please wait <span id="countdown">{{ cooldown_remaining|int }}</span> seconds to resend OTP.</p>
        {% else %}
          <form method="POST" action="{{ url_for('resend_otp') }}">
            <button type="submit">Resend OTP</button>
          </form>
        {% endif %}
        <script>
          var countdown = {{ cooldown_remaining|int }};
          if (countdown > 0) {
            var countdownElem = document.getElementById('countdown');
            var interval = setInterval(function() {
              countdown -= 1;
              countdownElem.textContent = countdown;
              if (countdown <= 0) {
                clearInterval(interval);
                location.reload();
              }
            }, 1000);
          }
        </script>
    ''', error=error, cooldown_remaining=cooldown_remaining)

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    now = time.time()
    otp_sent_time = session.get('otp_sent_time', 0)
    if now - otp_sent_time < OTP_RESEND_COOLDOWN:
        return redirect(url_for('verify'))
    email = session.get('email')
    if not email:
        return redirect(url_for('index'))
    otp = generate_otp()
    session['otp'] = otp
    session['otp_sent_time'] = now
    session['otp_attempts'] = 0
    send_otp(email, otp)
    return redirect(url_for('verify'))

if __name__ == '__main__':
    app.run(debug=True)

