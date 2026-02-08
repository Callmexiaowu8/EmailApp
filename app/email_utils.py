import smtplib
import time
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from flask import current_app

# Configure logging
logging.basicConfig(
    filename='email_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_email_with_attachment(subject, body, file_path, recipient):
    """
    Send an email with an attachment using SMTP.
    Includes retry mechanism and logging.
    """
    msg = MIMEMultipart()
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    if not sender:
        logging.error("MAIL_DEFAULT_SENDER not configured")
        return False

    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if file_path and os.path.exists(file_path):
        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {filename}")
                msg.attach(part)
        except Exception as e:
            logging.error(f"Failed to attach file: {e}")
            return False

    retries = 3
    for attempt in range(retries):
        try:
            # Check if server config exists
            if not current_app.config['MAIL_SERVER']:
                logging.error("MAIL_SERVER not configured")
                return False

            server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
            
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            
            if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
                server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            
            text = msg.as_string()
            server.sendmail(sender, recipient, text)
            server.quit()
            
            logging.info(f"Email sent successfully to {recipient}. Subject: {subject}")
            return True
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait before retry
            else:
                logging.error("All retry attempts failed.")
                return False
