from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, Email, Optional, ValidationError
from app.config import Config
from email_validator import validate_email, EmailNotValidError

def validate_multi_email(form, field):
    if not field.data:
        raise ValidationError('请输入收件人邮箱')
    
    emails = [e.strip() for e in field.data.replace('\r\n', '\n').split('\n') if e.strip()]
    if not emails:
        raise ValidationError('请输入收件人邮箱')
    
    for email in emails:
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            raise ValidationError(f'无效的邮箱地址: {email}')

class EmailForm(FlaskForm):
    recipient = StringField('收件人', validators=[DataRequired(message='请输入收件人邮箱'), validate_multi_email])
    subject = StringField('邮件主题', validators=[Optional()])
    content = TextAreaField('邮件正文', validators=[Optional()])
    file = FileField('添加附件', validators=[
        FileAllowed(Config.ALLOWED_EXTENSIONS, '不支持的文件类型！')
    ])
    submit = SubmitField('发送邮件')
