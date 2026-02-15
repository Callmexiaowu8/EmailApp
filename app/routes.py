from flask import Blueprint, current_app, request, render_template
from werkzeug.utils import secure_filename
import os
from app.email_utils import send_email_with_attachment

bp = Blueprint("main", __name__)


def render_index_page(message: str) -> str:
    """
    渲染首页表单页面。

    Args:
        message: 页面顶部展示的提示信息（错误或成功提示）。

    Returns:
        渲染后的 HTML 字符串。
    """
    return render_template("index.html", message=message)


def get_recipient_from_request() -> str | None:
    """
    获取收件人地址。

    优先使用表单字段 recipient；如果用户未填写，则尝试从应用配置 MAIL_RECIPIENT 获取。

    Returns:
        收件人邮箱地址；若无法获取则返回 None。
    """
    recipient = request.form.get("recipient")
    if recipient:
        return recipient
    return current_app.config.get("MAIL_RECIPIENT")


def get_content_from_request() -> str:
    """
    获取邮件正文内容。

    Returns:
        邮件正文字符串；若表单未提供则返回默认文案。
    """
    content = request.form.get("content")
    return content or "No content provided."


def save_uploaded_file() -> str | None:
    """
    处理并保存用户上传的附件文件。

    Returns:
        保存后的文件路径；若没有上传文件则返回 None。
    """
    file = request.files.get("file")
    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    return file_path


def cleanup_file(file_path: str | None) -> None:
    """
    清理临时上传文件。

    Args:
        file_path: 需要删除的文件路径；为 None 时不做任何处理。
    """
    if file_path and os.path.exists(file_path):
        os.remove(file_path)


@bp.route("/", methods=["GET"])
def index_get():
    """
    处理首页 GET 请求：返回邮件发送表单页面。

    Returns:
        HTML 页面字符串。
    """
    return render_index_page("")


@bp.route("/", methods=["POST"])
def index_post():
    """
    处理首页 POST 请求：接收表单数据，发送邮件（可选附件），并返回结果页面。

    Returns:
        HTML 页面字符串（包含发送结果提示）。
    """
    recipient = get_recipient_from_request()
    if not recipient:
        return render_index_page("Error: Recipient not configured and not provided in form.")

    content = get_content_from_request()

    file_path = None
    try:
        file_path = save_uploaded_file()
        success = send_email_with_attachment(
            subject="来自EmailApp的邮件",
            body=content,
            file_path=file_path,
            recipient=recipient,
        )
    finally:
        cleanup_file(file_path)

    if success:
        return render_index_page("Email sent successfully!")
    return render_index_page("Failed to send email. Check logs.")
