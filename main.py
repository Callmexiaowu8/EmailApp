from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import uuid
import re
import shutil
from typing import Optional, Dict, List
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

from models import (
    InlineImageUploadResponse,
    EmailSendResponse,
)
from email_utils import send_email_async, INLINE_IMAGE_RE
from dependencies import (
    get_upload_folder,
    get_inline_image_folder,
    get_max_content_length,
    get_default_sender,
    get_default_recipient,
    get_default_subject,
)

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), auto_reload=True)

app = FastAPI(
    title="邮件发送服务",
    description="基于 FastAPI 的邮件发送应用，支持富文本和附件",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

inline_image_folder = get_inline_image_folder()


def cleanup_file(path: Optional[str]):
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass


def cleanup_files(paths: List[Optional[str]]):
    for path in paths:
        cleanup_file(path)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    sender = get_default_sender()
    recipient = get_default_recipient()
    subject = get_default_subject()
    template = jinja_env.get_template("index.html")
    return HTMLResponse(template.render(request=request, sender=sender, default_recipient=recipient, default_subject=subject))


@app.post("/send", response_model=EmailSendResponse)
async def send_email(
    recipient: str = Form(...),
    subject: str = Form(""),
    content: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    recipients = [e.strip() for e in recipient.replace('\r\n', '\n').split('\n') if e.strip()]

    if not recipients:
        return EmailSendResponse(success=False, message="收件人邮箱未配置！")

    default_subject = get_default_subject()
    subject = subject.strip() or default_subject

    file_path = None
    inline_image_folder_path = get_inline_image_folder()

    try:
        if file and file.filename:
            upload_folder = get_upload_folder()
            file_path = upload_folder / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        html_content = content
        inline_images: Dict[str, str] = {}

        # Parse HTML to find inline images with data-inline-id attribute
        # Pattern matches: <img ... src="/inline-images/xxx.png" ... data-inline-id="xxx.png" ...>
        img_pattern = re.compile(
            r'<img\s+[^>]*?src="/inline-images/([0-9a-f]{32}\.(?:png|jpg|jpeg|gif))"[^>]*?data-inline-id="([0-9a-f]{32}\.(?:png|jpg|jpeg|gif))"[^>]*?>',
            re.IGNORECASE
        )

        # Find all inline images in the HTML
        for match in img_pattern.finditer(html_content):
            src_id = match.group(1)
            data_id = match.group(2)
            # Only process if src and data-inline-id match
            if src_id == data_id:
                inline_path = inline_image_folder_path / data_id
                if inline_path.exists():
                    inline_images[data_id] = str(inline_path)

        # Replace src attributes with cid: references for found inline images
        for inline_id in inline_images:
            html_content = html_content.replace(
                f'src="/inline-images/{inline_id}"',
                f'src="cid:{inline_id}"'
            )

        success = await send_email_async(
            subject=subject,
            body="",
            recipients=recipients,
            file_path=str(file_path) if file_path else None,
            inline_images=inline_images if inline_images else None,
            body_html=html_content
        )

        if success:
            return EmailSendResponse(success=True, message="邮件发送成功！")
        else:
            return EmailSendResponse(success=False, message="邮件发送失败，请查看日志。")

    except Exception as e:
        return EmailSendResponse(success=False, message=f"发送失败: {str(e)}")

    finally:
        cleanup_file(str(file_path) if file_path else None)


@app.post("/api/inline-images", response_model=InlineImageUploadResponse)
async def upload_inline_image(file: UploadFile = File(...)):
    if not file.filename:
        return InlineImageUploadResponse(ok=False, error="未找到图片文件")

    content_type = file.content_type or ""
    if not content_type.startswith('image/'):
        return InlineImageUploadResponse(ok=False, error="不支持的图片类型")

    max_length = get_max_content_length()
    content_length = file.size or 0
    if content_length > max_length:
        return InlineImageUploadResponse(
            ok=False,
            error=f"文件大小超过限制 ({max_length // (1024 * 1024)}MB)"
        )

    ext = os.path.splitext(file.filename)[1].lstrip('.').lower()
    if ext == 'jpeg':
        ext = 'jpg'
    if ext not in {'png', 'jpg', 'gif'}:
        return InlineImageUploadResponse(ok=False, error="仅支持 PNG / JPG / GIF")

    image_id = uuid.uuid4().hex
    filename = f'{image_id}.{ext}'
    folder = get_inline_image_folder()
    file_path = folder / filename

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return InlineImageUploadResponse(
            ok=True,
            id=filename,
            url=f"/inline-images/{filename}"
        )
    except Exception as e:
        return InlineImageUploadResponse(ok=False, error=f"上传失败: {str(e)}")


@app.get("/inline-images/{filename}")
async def get_inline_image(filename: str):
    if not INLINE_IMAGE_RE.match(filename):
        raise HTTPException(status_code=404, detail="文件不存在")

    folder = get_inline_image_folder()
    file_path = folder / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    ext = filename.split('.')[-1].lower()
    if ext == 'jpg':
        ext = 'jpeg'

    return FileResponse(
        file_path,
        media_type=f"image/{ext}",
        headers={"Content-Disposition": "inline"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
