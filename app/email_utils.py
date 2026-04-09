import smtplib
import time
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import os
import uuid
from html.parser import HTMLParser
from flask import current_app
from app.utils import INLINE_IMAGE_RE

logging.basicConfig(
    filename='email_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class _InlineImageRewriter(HTMLParser):
    def __init__(self, inline_dir):
        super().__init__(convert_charrefs=True)
        self.inline_dir = inline_dir
        self.parts = []
        self.images = []
        self._skip_script = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'script':
            self._skip_script = True
            return
        if tag.lower() == 'img':
            self._handle_img(attrs, self_closing=False)
            return
        self._emit_tag(tag, attrs, closed=False)

    def handle_startendtag(self, tag, attrs):
        if tag.lower() == 'script':
            return
        if tag.lower() == 'img':
            self._handle_img(attrs, self_closing=True)
            return
        self._emit_tag(tag, attrs, closed=True)

    def handle_endtag(self, tag):
        if tag.lower() == 'script':
            self._skip_script = False
            return
        self.parts.append(f"</{tag}>")

    def handle_data(self, data):
        if self._skip_script:
            return
        self.parts.append(data)

    def handle_entityref(self, name):
        self.parts.append(f"&{name};")

    def handle_charref(self, name):
        self.parts.append(f"&#{name};")

    def _emit_tag(self, tag, attrs, closed):
        a = []
        for k, v in (attrs or []):
            if (k or '').lower().startswith('on'):
                continue
            if v is None:
                a.append(k)
            else:
                q = '"' if '"' not in v else "'"
                a.append(f"{k}={q}{v}{q}")
        joined = (" " + " ".join(a)) if a else ""
        if closed:
            self.parts.append(f"<{tag}{joined} />")
        else:
            self.parts.append(f"<{tag}{joined}>")

    def _handle_img(self, attrs, self_closing):
        attr_map = {k: v for k, v in (attrs or [])}
        inline_id = (attr_map.get('data-inline-id') or '').strip()
        src = (attr_map.get('src') or '').strip()
        filename = inline_id or os.path.basename(src)

        cid = None
        path = None
        if filename and INLINE_IMAGE_RE.match(filename):
            candidate = os.path.join(self.inline_dir, filename)
            if os.path.exists(candidate):
                cid = f"{uuid.uuid4().hex}@inline"
                path = candidate

        out_attrs = []
        for k, v in (attrs or []):
            if (k or '').lower().startswith('on'):
                continue
            if k == 'data-inline-id':
                continue
            if k == 'src' and cid:
                out_attrs.append((k, f"cid:{cid}"))
            else:
                out_attrs.append((k, v))

        self._emit_tag('img', out_attrs, closed=True)
        if cid and path:
            self.images.append({'cid': cid, 'path': path})

    def result(self):
        return "".join(self.parts), self.images

class _HtmlTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in {'br', 'p', 'div', 'li'}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not data:
            return
        self.parts.append(data)

    def get_text(self):
        text = "".join(self.parts)
        lines = [ln.strip() for ln in text.splitlines()]
        return "\n".join([ln for ln in lines if ln])

def _guess_image_subtype(path):
    ext = os.path.splitext(path)[1].lstrip('.').lower()
    if ext == 'jpg':
        return 'jpeg'
    if ext in {'jpeg', 'png', 'gif'}:
        return ext
    return 'octet-stream'

def send_email_with_attachment(subject, body, file_path, recipients, body_html=None, inline_images=None):
    """
    使用 SMTP 发送带附件的邮件。
    包含重试机制和日志记录。
    支持多个收件人。
    """
    sender = current_app.config['MAIL_DEFAULT_SENDER']
    if not sender:
        logging.error("MAIL_DEFAULT_SENDER not configured")
        return False

    if body_html:
        inline_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'inline_images')
        rewriter = _InlineImageRewriter(inline_dir)
        rewriter.feed(body_html)
        rewritten_html, found_images = rewriter.result()
        extracted = _HtmlTextExtractor()
        extracted.feed(rewritten_html)
        plain_text = body if body else extracted.get_text()

        msg = MIMEMultipart('mixed')
        related = MIMEMultipart('related')
        alternative = MIMEMultipart('alternative')
        alternative.attach(MIMEText(plain_text, 'plain', 'utf-8'))
        alternative.attach(MIMEText(rewritten_html, 'html', 'utf-8'))
        related.attach(alternative)

        for item in (inline_images or found_images):
            try:
                path = item['path']
                cid = item['cid']
                subtype = _guess_image_subtype(path)
                if subtype == 'octet-stream':
                    continue
                with open(path, 'rb') as f:
                    part = MIMEImage(f.read(), _subtype=subtype)
                part.add_header('Content-ID', f"<{cid}>")
                part.add_header('Content-Disposition', 'inline', filename=os.path.basename(path))
                related.attach(part)
            except Exception as e:
                logging.error(f"Failed to attach inline image: {e}")
                return False

        msg.attach(related)
    else:
        msg = MIMEMultipart()
        msg.attach(MIMEText(body or '', 'plain', 'utf-8'))

    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject

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
            if not current_app.config['MAIL_SERVER']:
                logging.error("MAIL_SERVER not configured")
                return False

            server = smtplib.SMTP(current_app.config['MAIL_SERVER'], current_app.config['MAIL_PORT'])
            
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            
            if current_app.config['MAIL_USERNAME'] and current_app.config['MAIL_PASSWORD']:
                server.login(current_app.config['MAIL_USERNAME'], current_app.config['MAIL_PASSWORD'])
            
            text = msg.as_string()
            server.sendmail(sender, recipients, text)
            server.quit()
            
            logging.info(f"Email sent successfully to {recipients}. Subject: {subject}")
            return True
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < retries - 1:
                time.sleep(2)
            else:
                logging.error("All retry attempts failed.")
                return False
