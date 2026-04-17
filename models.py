from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
import re


class EmailFormRequest(BaseModel):
    recipient: str = Field(..., description="收件人邮箱，多个用换行分隔")
    subject: Optional[str] = Field(None, description="邮件主题")
    content: str = Field(..., description="邮件正文")
    file_name: Optional[str] = Field(None, description="附件文件名")

    @field_validator('recipient')
    @classmethod
    def validate_recipient(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('请输入收件人邮箱')
        return v.strip()

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        return v.strip() if v else v

    def get_recipients_list(self) -> List[str]:
        return [e.strip() for e in self.recipient.replace('\r\n', '\n').split('\n') if e.strip()]


class InlineImageUploadResponse(BaseModel):
    ok: bool
    id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    success: bool = True


class EmailSendResponse(BaseModel):
    success: bool
    message: str
