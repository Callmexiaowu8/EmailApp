import smtplib
import time
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from flask import current_app

# 配置日志记录
logging.basicConfig(
    filename='email_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_email_with_attachment(subject, body, file_path, recipient, smtp_config=None):
    """
    使用 SMTP 发送带附件的邮件。
    包含重试机制和日志记录。
    """
    def get_config_value(key, default=None):
        if smtp_config is not None and key in smtp_config and smtp_config[key] is not None:
            return smtp_config[key]
        return current_app.config.get(key, default)

    msg = MIMEMultipart()
    sender = get_config_value('MAIL_DEFAULT_SENDER')
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
            mail_server = get_config_value('MAIL_SERVER')
            mail_port = int(get_config_value('MAIL_PORT') or 0)
            mail_use_tls = bool(get_config_value('MAIL_USE_TLS', True))
            mail_username = get_config_value('MAIL_USERNAME')
            mail_password = get_config_value('MAIL_PASSWORD')

            if not mail_server:
                logging.error("MAIL_SERVER not configured")
                return False
            if not mail_port:
                logging.error("MAIL_PORT not configured")
                return False

            server = smtplib.SMTP(mail_server, mail_port)
            
            if mail_use_tls:
                server.starttls()
            
            if mail_username and mail_password:
                server.login(mail_username, mail_password)
            
            text = msg.as_string()
            server.sendmail(sender, recipient, text)
            server.quit()
            
            logging.info(f"Email sent successfully to {recipient}. Subject: {subject}")
            return True
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(2)  # 重试前等待
            else:
                logging.error("All retry attempts failed.")
                return False
