import smtplib
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import os
import uuid
from html.parser import HTMLParser
from typing import Optional, List, Dict, Any
import re

logging.basicConfig(
    filename='email_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

INLINE_IMAGE_RE = re.compile(r'^[0-9a-f]{32}\.(png|jpg|jpeg|gif)$', re.IGNORECASE)


class InlineImageRewriter(HTMLParser):
    def __init__(self, inline_images: Dict[str, str]):
        super().__init__()
        self.inline_images = inline_images
        self.output = []
        self._in_img_tag = False
        self._current_src = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            src = dict(attrs).get('src', '')
            if src and src.startswith('inline://'):
                inline_id = src.replace('inline://', '')
                if inline_id in self.inline_images:
                    self.output.append(f'<img src="cid:{inline_id}"')
                    return
            for attr in attrs:
                if attr[0] == 'src':
                    self._current_src = attr[1]
                    self._in_img_tag = True
                    self.output.append(f'<img ')
                    self.output.append(f'src="{attr[1]}" ')
                else:
                    self.output.append(f'{attr[0]}="{attr[1]}" ')
        else:
            self.output.append(f'<{tag} ')
            for attr in attrs:
                self.output.append(f'{attr[0]}="{attr[1]}" ')
            self.output.append('>')

    def handle_endtag(self, tag):
        if tag == 'img' and not self._in_img_tag:
            pass
        elif tag == 'img' and self._in_img_tag:
            self._in_img_tag = False
            self.output.append('/>')
        else:
            self.output.append(f'</{tag}>')

    def handle_data(self, data):
        self.output.append(data)

    def get_output(self):
        return ''.join(self.output)


async def send_email_async(
    subject: str,
    body: str,
    recipients: List[str],
    file_path: Optional[str] = None,
    inline_images: Optional[Dict[str, str]] = None,
    body_html: Optional[str] = None
) -> bool:
    sender = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    mail_server = os.getenv('MAIL_SERVER', 'smtp.example.com')
    mail_port = int(os.getenv('MAIL_PORT', 587))
    mail_username = os.getenv('MAIL_USERNAME', '')
    mail_password = os.getenv('MAIL_PASSWORD', '')
    mail_use_tls = os.getenv('MAIL_USE_TLS', 'true').lower() in ('true', '1', 'on')

    msg = MIMEMultipart('related')
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject

    if body_html:
        if inline_images:
            rewriter = InlineImageRewriter(inline_images)
            rewriter.feed(body_html)
            body_html = rewriter.get_output()

        msg.attach(MIMEText(body_html, 'html'))

        if body:
            msg.attach(MIMEText(body, 'plain'))
    else:
        msg.attach(MIMEText(body, 'plain'))

    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(file_path)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

    if inline_images:
        for inline_id, filepath in inline_images.items():
            if os.path.exists(filepath) and INLINE_IMAGE_RE.match(inline_id):
                ext = os.path.splitext(filepath)[1].lstrip('.').lower()
                if ext == 'jpg':
                    ext = 'jpeg'
                with open(filepath, 'rb') as f:
                    img = MIMEImage(f.read(), _subtype=ext)
                img.add_header('Content-ID', f'<{inline_id}>')
                img.add_header('Content-Disposition', 'inline')
                msg.attach(img)

    retries = 3
    for attempt in range(retries):
        try:
            if mail_use_tls:
                server = smtplib.SMTP(mail_server, mail_port, timeout=30)
                server.ehlo()
                server.starttls()
            else:
                server = smtplib.SMTP(mail_server, mail_port, timeout=30)

            server.login(mail_username, mail_password)
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()

            logging.info(f"Email sent successfully to {recipients}. Subject: {subject}")
            return True
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                await asyncio.sleep(2)
            else:
                logging.error("All retry attempts failed.")
                return False

    return False
