from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request
from werkzeug.utils import secure_filename
import os
from app.forms import EmailForm
from app.email_utils import send_email_with_attachment

bp = Blueprint('main', __name__)

@bp.route('/', methods=['GET', 'POST'])
def index():
    form = EmailForm()
    
    # 默认填充收件人
    if request.method == 'GET' and not form.recipient.data:
        form.recipient.data = current_app.config.get('MAIL_RECIPIENT')

    if form.validate_on_submit():
        recipient = form.recipient.data
        text_content = form.content.data
        file = form.file.data
        file_path = None

        if file:
            filename = secure_filename(file.filename)
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
        
        # recipient = current_app.config['MAIL_RECIPIENT'] # Already got from form
        if not recipient:
            flash('Recipient email not configured!', 'danger')
            return redirect(url_for('main.index'))

        success = send_email_with_attachment(
            subject="New Submission from EmailApp",
            body=text_content,
            file_path=file_path,
            recipient=recipient
        )

        if success:
            flash('Email sent successfully!', 'success')
        else:
            flash('Failed to send email. Check logs.', 'danger')
        
        # Clean up uploaded file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            
        return redirect(url_for('main.index'))
    
    sender = current_app.config.get('MAIL_DEFAULT_SENDER')
    return render_template('index.html', form=form, sender=sender)
