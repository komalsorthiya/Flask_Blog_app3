from flask import request
import os
import smtplib  # This helps us send emails
from email.mime.text import MIMEText  # This helps us create email messages
from email.mime.multipart import MIMEMultipart  # This helps us create email messages with different parts

# This function sends password reset emails
def send_reset_email(user, token):
    # Create a new email message
    msg = MIMEMultipart()
    msg['From'] = os.getenv('EMAIL_USER')  # Who the email is from
    msg['To'] = user.email  # Who to send it to
    msg['Subject'] = 'Password Reset Request'  # The email subject
    
    # Create the link to reset the password
    reset_url = f"{request.host_url}reset_password/{token}"
    
    # Write the email message
    body = f"""
    Hello {user.username},
    
    You requested a password reset. Click the link below to reset your password:
    {reset_url}
    
    This link will expire in 1 hour.
    
    If you didn't request this, please ignore this email.
    """
    
    # Add the message to the email
    msg.attach(MIMEText(body, 'plain'))
    
    # Send the email
    with smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT'))) as server:
        server.starttls()  # Make the connection secure
        server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))  # Log in to the email server
        server.send_message(msg)  # Send the email