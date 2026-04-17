import os
from pathlib import Path
from typing import Optional
from functools import lru_cache


@lru_cache()
def get_upload_folder() -> Path:
    folder = os.getenv('UPLOAD_FOLDER', 'uploads')
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_inline_image_folder() -> Path:
    base = get_upload_folder()
    folder = base / 'inline_images'
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_max_content_length() -> int:
    return int(os.getenv('MAX_CONTENT_LENGTH', 30 * 1024 * 1024))


def get_default_sender() -> str:
    return os.getenv('MAIL_DEFAULT_SENDER', '')


def get_default_recipient() -> str:
    return os.getenv('MAIL_RECIPIENT', '')


def get_default_subject() -> str:
    return os.getenv('MAIL_DEFAULT_SUBJECT', '一封邮件📧')


def get_allowed_extensions() -> set:
    default = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
    extensions_str = os.getenv('ALLOWED_EXTENSIONS', '')
    if extensions_str:
        return set(ext.strip().lower() for ext in extensions_str.split(','))
    return default
