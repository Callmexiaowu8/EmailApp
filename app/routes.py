from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os

from sqlalchemy import select, update

from app.db import get_session
from app.email_utils import send_email_with_attachment
from app.models import EmailAccount, User

bp = Blueprint("main", __name__)


def render_index_page(message: str) -> str:
    """
    渲染首页表单页面。

    Args:
        message: 页面顶部展示的提示信息（错误或成功提示）。

    Returns:
        渲染后的 HTML 字符串。
    """
    return render_template("index.html", message=message, user=get_current_user())


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


def get_current_user() -> User | None:
    """
    获取当前登录用户。

    Returns:
        登录用户对象；未登录则返回 None。
    """
    user_id = session.get("user_id")
    if not user_id:
        return None

    db = get_session()
    return db.scalar(select(User).where(User.id == user_id))


def login_required(view_func):
    """
    视图装饰器：要求用户已登录，否则跳转到登录页。
    """
    @wraps(view_func)
    def _wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("main.login"))
        return view_func(*args, **kwargs)

    return _wrapped


def get_user_default_email_account(user_id: int) -> EmailAccount | None:
    """
    获取用户默认启用的邮箱配置。

    Args:
        user_id: 用户 ID。

    Returns:
        默认邮箱配置；若不存在则返回 None。
    """
    db = get_session()
    stmt = (
        select(EmailAccount)
        .where(EmailAccount.user_id == user_id)
        .where(EmailAccount.is_default == 1)
        .where(EmailAccount.status == 1)
        .where(EmailAccount.deleted_at.is_(None))
        .limit(1)
    )
    return db.scalar(stmt)



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
        smtp_config = None
        user = get_current_user()
        if user is not None:
            account = get_user_default_email_account(user.id)
            if account is not None:
                smtp_config = {
                    "MAIL_SERVER": account.smtp_server,
                    "MAIL_PORT": int(account.smtp_port),
                    "MAIL_USE_TLS": bool(account.use_tls),
                    "MAIL_USERNAME": account.email,
                    "MAIL_PASSWORD": account.auth_code,
                    "MAIL_DEFAULT_SENDER": account.email,
                }
        success = send_email_with_attachment(
            subject="来自EmailApp的邮件",
            body=content,
            file_path=file_path,
            recipient=recipient,
            smtp_config=smtp_config,
        )
    finally:
        cleanup_file(file_path)

    if success:
        return render_index_page("Email sent successfully!")
    return render_index_page("Failed to send email. Check logs.")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """
    用户登录页面：GET 返回表单，POST 校验账号密码并写入 session。
    """
    message = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        if not username or not password:
            message = "用户名和密码不能为空。"
        else:
            db = get_session()
            user = db.scalar(select(User).where(User.username == username))
            if user is None or not check_password_hash(user.password_hash, password):
                message = "用户名或密码错误。"
            elif user.is_active != 1:
                message = "账号已被禁用。"
            else:
                session["user_id"] = user.id
                user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
                db.commit()
                return redirect(url_for("main.index_get"))

    return render_template("login.html", message=message)


@bp.route("/logout", methods=["GET"])
def logout():
    """
    退出登录：清空 session 并返回首页。
    """
    session.pop("user_id", None)
    return redirect(url_for("main.index_get"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """
    用户注册页面：创建登录账号。
    """
    message = ""
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        if not username or not password:
            message = "用户名和密码不能为空。"
        elif password != confirm:
            message = "两次输入的密码不一致。"
        else:
            db = get_session()
            exists = db.scalar(select(User.id).where(User.username == username))
            if exists is not None:
                message = "用户名已存在。"
            else:
                user = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                    is_active=1,
                )
                db.add(user)
                db.commit()
                session["user_id"] = user.id
                return redirect(url_for("main.index_get"))

    return render_template("register.html", message=message)


@bp.route("/settings/email", methods=["GET", "POST"])
@login_required
def email_settings():
    """
    邮箱配置页面：登录用户可配置自己的 SMTP 信息与授权码。
    """
    user = get_current_user()
    db = get_session()
    account = None
    if user is not None:
        account = get_user_default_email_account(user.id) or db.scalar(
            select(EmailAccount)
            .where(EmailAccount.user_id == user.id)
            .where(EmailAccount.deleted_at.is_(None))
            .limit(1)
        )

    message = ""
    if request.method == "POST" and user is not None:
        email = (request.form.get("email") or "").strip()
        smtp_server = (request.form.get("smtp_server") or "").strip()
        smtp_port_raw = (request.form.get("smtp_port") or "587").strip()
        use_tls = 1 if request.form.get("use_tls") == "on" else 0
        auth_code = request.form.get("auth_code") or ""
        is_default = 1 if request.form.get("is_default") == "on" else 0

        try:
            smtp_port = int(smtp_port_raw)
        except ValueError:
            smtp_port = -1

        if not email or not smtp_server or not auth_code or not (0 < smtp_port <= 65535):
            message = "请填写完整信息（邮箱、SMTP 服务器、端口、授权码）。"
        else:
            if account is None:
                account = EmailAccount(
                    user_id=user.id,
                    email=email,
                    smtp_server=smtp_server,
                    smtp_port=smtp_port,
                    use_tls=use_tls,
                    auth_code=auth_code,
                    is_default=is_default,
                    status=1,
                )
                db.add(account)
            else:
                account.email = email
                account.smtp_server = smtp_server
                account.smtp_port = smtp_port
                account.use_tls = use_tls
                account.auth_code = auth_code
                account.is_default = is_default
                account.status = 1
                account.deleted_at = None

            if is_default == 1:
                db.execute(
                    update(EmailAccount)
                    .where(EmailAccount.user_id == user.id)
                    .values(is_default=0)
                )
                account.is_default = 1

            db.commit()
            message = "保存成功。"

    return render_template("email_settings.html", message=message, user=user, account=account)
