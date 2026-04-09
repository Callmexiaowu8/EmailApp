from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
import os
import re
import uuid
from app.forms import EmailForm
from app.email_utils import send_email_with_attachment
from app.utils import INLINE_IMAGE_RE

bp = Blueprint('main', __name__)

def _inline_image_folder():
    base = current_app.config['UPLOAD_FOLDER']
    folder = os.path.abspath(os.path.join(base, 'inline_images'))
    if not os.path.exists(folder):
        os.makedirs(folder)
    return folder

@bp.post('/api/inline-images')
def upload_inline_image():
    file = request.files.get('image')
    if not file or not file.filename:
        return jsonify(ok=False, error='未找到图片文件'), 400

    if not (file.mimetype or '').startswith('image/'):
        return jsonify(ok=False, error='不支持的图片类型'), 400

    content_length = request.content_length or 0
    max_length = current_app.config.get('MAX_CONTENT_LENGTH', 30 * 1024 * 1024)
    if content_length > max_length:
        return jsonify(ok=False, error=f'文件大小超过限制 ({max_length // (1024 * 1024)}MB)'), 400

    ext = os.path.splitext(file.filename)[1].lstrip('.').lower()
    if ext == 'jpeg':
        ext = 'jpg'
    if ext not in {'png', 'jpg', 'gif'}:
        return jsonify(ok=False, error='仅支持 PNG / JPG / GIF'), 400

    image_id = uuid.uuid4().hex
    filename = f'{image_id}.{ext}'
    folder = _inline_image_folder()
    file.save(os.path.join(folder, filename))

    return jsonify(ok=True, id=filename, url=url_for('main.inline_image', filename=filename))

@bp.get('/inline-images/<path:filename>')
def inline_image(filename):
    if not filename or not INLINE_IMAGE_RE.match(filename):
        abort(404)
    folder = _inline_image_folder()
    return send_from_directory(folder, filename)

@bp.route('/', methods=['GET', 'POST'])
def index():
    form = EmailForm()
    default_subject = current_app.config.get('MAIL_DEFAULT_SUBJECT') or 'New Submission from EmailApp'
    
    # 默认填充收件人
    if request.method == 'GET' and not form.recipient.data:
        form.recipient.data = current_app.config.get('MAIL_RECIPIENT')
    # 主题默认为空，由用户自行填写

    if form.validate_on_submit():
        recipient_raw = form.recipient.data
        recipients = [e.strip() for e in recipient_raw.replace('\r\n', '\n').split('\n') if e.strip()]
        subject = (form.subject.data or '').strip() or default_subject
        text_content = form.content.data
        file = form.file.data
        file_path = None
        inline_paths = []

        if file:
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
        
        if not recipients:
            flash('收件人邮箱未配置！', 'danger')
            return redirect(url_for('main.index'))

        inline_ids = set()
        inline_ids.update(re.findall(r'data-inline-id=["\']([^"\']+)["\']', text_content or '', flags=re.IGNORECASE))
        inline_ids.update(re.findall(r'/inline-images/([0-9a-f]{32}\.(?:png|jpg|jpeg|gif))', text_content or '', flags=re.IGNORECASE))
        folder = _inline_image_folder()
        for inline_id in inline_ids:
            if INLINE_IMAGE_RE.match(inline_id):
                inline_paths.append(os.path.join(folder, inline_id))

        try:
            success = send_email_with_attachment(
                subject=subject,
                body="",
                body_html=text_content,
                file_path=file_path,
                recipients=recipients
            )
        finally:
            for p in inline_paths:
                if p and os.path.exists(p):
                    os.remove(p)

        if success:
            flash('邮件发送成功！', 'success')
        else:
            flash('邮件发送失败，请查看日志。', 'danger')
        
        # 清理上传的文件
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        return redirect(url_for('main.index'))
    
    sender = current_app.config.get('MAIL_DEFAULT_SENDER')
    return render_template('index.html', form=form, sender=sender, default_subject=default_subject)
