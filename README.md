# 邮件发送服务

<br />

lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 1; cd /Users/lian/GitHub/EmailApp && nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000

<br />

基于 FastAPI 的现代化邮件发送 Web 服务，提供用户友好的网页界面，支持富文本编辑、附件上传和异步邮件发送。

## 功能特性

- **现代 Web 界面**：使用 Bootstrap 5 构建的整洁、响应式网页表单
- **富文本编辑**：支持在邮件正文中直接粘贴或拖拽插入图片
- **附件上传**：支持 PDF、图片、Word 等多种文件类型（最大 16MB）
- **异步邮件发送**：使用 SMTP 协议发送邮件，支持自动重试
- **自动 API 文档**：基于 FastAPI 自动生成的 Swagger UI 和 ReDoc
- **类型安全**：完整的 Pydantic 模型验证

## 技术栈

- **框架**：FastAPI + Starlette
- **模板引擎**：Jinja2
- **邮件处理**：Python smtplib + email
- **依赖管理**：uv

## 环境要求

- Python 3.12+
- `uv` 包管理器

## 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置 SMTP 相关选项。

### 2. 启动服务

```bash
uv sync
uv run uvicorn main:app --reload --port 8000
```

### 3. 访问应用

- **主页**：<http://localhost:8000>
- **Swagger API 文档**：<http://localhost:8000/docs>
- **ReDoc 文档**：<http://localhost:8000/redoc>

## 项目结构

```
EmailApp/
├── main.py            # FastAPI 应用入口 & 路由
├── models.py          # Pydantic 请求/响应模型
├── dependencies.py     # 依赖注入函数
├── email_utils.py     # 异步邮件发送逻辑
├── static/            # 静态资源
│   ├── style.css     # 页面样式
│   └── compose_editor.js  # 富文本编辑器逻辑
├── templates/         # Jinja2 模板
│   └── index.html    # 主页面模板
├── .env.example      # 环境变量模板
├── pyproject.toml    # 项目配置 & 依赖
└── README.md         # 本文件
```

## API 端点

| 方法   | 路径                          | 说明         |
| ---- | --------------------------- | ---------- |
| GET  | `/`                         | 主页面        |
| POST | `/send`                     | 发送邮件       |
| POST | `/api/inline-images`        | 上传内嵌图片     |
| GET  | `/inline-images/{filename}` | 获取内嵌图片     |
| GET  | `/docs`                     | Swagger UI |
| GET  | `/redoc`                    | ReDoc      |

## 环境变量说明

| 变量名                    | 说明          | 必填 |
| ---------------------- | ----------- | -- |
| `MAIL_SERVER`          | SMTP 服务器地址  | 是  |
| `MAIL_PORT`            | SMTP 端口     | 是  |
| `MAIL_USE_TLS`         | 是否启用 TLS    | 是  |
| `MAIL_USERNAME`        | SMTP 用户名    | 是  |
| `MAIL_PASSWORD`        | SMTP 密码/授权码 | 是  |
| `MAIL_DEFAULT_SENDER`  | 默认发件人       | 是  |
| `MAIL_RECIPIENT`       | 默认收件人       | 否  |
| `MAIL_DEFAULT_SUBJECT` | 默认邮件主题      | 否  |
| `SECRET_KEY`           | 安全密钥        | 是  |
| `MAX_CONTENT_LENGTH`   | 最大上传大小（字节）  | 否  |
| `UPLOAD_FOLDER`        | 上传文件保存目录    | 否  |

## 许可证

MIT License
