from flask import Blueprint, current_app, request, jsonify
from werkzeug.utils import secure_filename
import os
from app.email_utils import send_email_with_attachment

bp = Blueprint("main", __name__)


@bp.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        """
        接收表单提交，执行邮件发送逻辑。
        """
        # 获取表单数据
        recipient = request.form.get("recipient")
        content = request.form.get("content")
        file = request.files.get("file")

        # 如果表单未提供收件人，尝试从配置获取
        if not recipient:
            recipient = current_app.config.get("MAIL_RECIPIENT")

        if not recipient:
            message = "Error: Recipient not configured and not provided in form."
        else:
            if not content:
                content = "No content provided."

            file_path = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

            # 调用核心后端功能
            success = send_email_with_attachment(
                subject="Email from Raw Frontend",
                body=content,
                file_path=file_path,
                recipient=recipient,
            )

            # 清理上传的文件
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

            if success:
                message = "Email sent successfully!"
            else:
                message = "Failed to send email. Check logs."

    # 返回表单和消息
    return f"""
    <div style="color: red;">{message}</div>
    <form action="/" method="post" enctype="multipart/form-data">
        收件人: <input type="text" name="recipient"><br>
        内容: <textarea name="content"></textarea><br>
        附件: <input type="file" name="file"><br>
        <input type="submit" value="发送">
    </form>
    """
