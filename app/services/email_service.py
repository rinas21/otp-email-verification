import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import Config

def send_otp_email(email, otp):
    """Send OTP via email"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['Subject'] = 'Your Secure Verification Code'
        msg['From'] = Config.SENDER_EMAIL
        msg['To'] = email

        # Email body with HTML formatting
        html = f'''
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                    <h2 style="color: #5469d4; text-align: center;">Your Verification Code</h2>
                    <p>Please use the following code to complete your verification:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <div style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #1e293b; background: #f8fafc; padding: 15px; border-radius: 5px; display: inline-block;">{otp}</div>
                    </div>
                    <p>This code will expire in 5 minutes.</p>
                    <p>If you didn't request this code, please ignore this email.</p>
                    <p style="font-size: 12px; color: #666; margin-top: 30px; text-align: center;">This is an automated message, please do not reply.</p>
                </div>
            </body>
        </html>
        '''
        
        msg.attach(MIMEText(html, 'html'))

        # Connect to server and send
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SENDER_EMAIL, Config.SENDER_PASSWORD)
            server.send_message(msg)
            
        return True, "OTP sent successfully!"
    except Exception as e:
        return False, f"Failed to send OTP: {str(e)}"