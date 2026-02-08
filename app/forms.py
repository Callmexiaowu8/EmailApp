from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, Email
from app.config import Config

class EmailForm(FlaskForm):
    recipient = StringField('收件人', validators=[DataRequired(message='请输入收件人邮箱'), Email(message='请输入有效的邮箱地址')])
    content = TextAreaField('邮件正文', validators=[DataRequired(message='请输入邮件内容')])
    file = FileField('添加附件', validators=[
        FileAllowed(Config.ALLOWED_EXTENSIONS, '不支持的文件类型！')
    ])
    submit = SubmitField('发送邮件')
