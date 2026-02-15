import os
from dotenv import load_dotenv

# 将项目根目录（或当前工作目录）下的 .env 文件加载到环境变量中，
# 使得 os.environ.get(...) 能读取到 .env 里配置的值。
load_dotenv()

class Config:
    # Flask 用于会话（session）签名等安全相关功能的密钥：
    # 生产环境务必在环境变量/ .env 中配置随机且足够长的 SECRET_KEY。
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'

    # SMTP 邮件服务器配置（用于发送邮件）
    # 例如：MAIL_SERVER=smtp.gmail.com
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    # SMTP 端口：常见 587（STARTTLS）、465（SMTPS）
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    # 是否启用 TLS：从字符串环境变量转换为 bool（true/on/1 均视为 True）
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    # SMTP 登录用户名/密码（敏感信息建议只放在环境变量或 .env，不要写死在代码里）
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # 默认发件人邮箱地址
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    # 默认收件人邮箱地址（表单未填写时使用）
    MAIL_RECIPIENT = os.environ.get('MAIL_RECIPIENT')

    # 上传请求体最大大小（字节），默认 20MB；超过会被 Flask 拒绝（通常 413）
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH') or 20 * 1024 * 1024)
    # 上传文件保存目录（默认 uploads）
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    # 允许上传的文件扩展名集合（扩展名不含点，如 txt、pdf）
    # 注意：包含 '*' 通常表示允许所有扩展名；对外服务时建议谨慎配置以降低风险。
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
        'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z', 
        'mp3', 'mp4', 'csv', 'json', 'xml', 
        '*'
    }
