# 邮件发送服务

这是一个基于 Python 开发的 Web 服务，提供用户友好的网页界面，用于发送包含附件的邮件。该项目使用 Flask 框架和标准 Python 库构建。

## 功能特性

- **用户界面**：使用 Bootstrap 5 构建的整洁、响应式网页表单。
- **文件上传**：支持多种文件类型（PDF、图片、文档等），最大支持 16MB。
- **邮件发送**：使用 SMTP 协议发送邮件，并在失败时自动重试（默认 3 次）。
- **日志记录**：详细的交易日志，用于审计和调试。
- **安全防护**：包含 CSRF 保护、安全文件名处理和输入验证。
- **环境管理**：使用 `uv` 进行依赖管理。

## 环境要求

- Python 3.12+
- `uv` 包管理器

## 安装步骤

1. **克隆仓库：**
   ```bash
   git clone <repository-url>
   cd EmailApp
   ```

2. **初始化环境并安装依赖：**
   ```bash
   uv sync
   ```
   或者手动安装：
   ```bash
   uv init
   uv add flask flask-wtf python-dotenv gunicorn
   ```

3. **配置：**
   复制 `.env.example`（或直接创建 `.env`）并配置您的 SMTP 设置。
   ```bash
   cp .env .env.local
   ```
   
   编辑 `.env` 文件：
   ```ini
   SECRET_KEY=your-secure-secret-key
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-password
   MAIL_DEFAULT_SENDER=sender@example.com
   MAIL_RECIPIENT=recipient@example.com  # 接收邮件的目标邮箱地址
   MAX_CONTENT_LENGTH=16777216  # 16MB (以字节为单位)
   UPLOAD_FOLDER=uploads
   ```

## 本地运行

启动开发服务器：

```bash
uv run python app.py
```

在浏览器中访问 `http://127.0.0.1:5000`。

## 运行测试

使用 `pytest` 运行测试套件：

```bash
uv run python -m pytest
```

## 部署

### 使用 Gunicorn (生产环境推荐)

本应用已准备好使用 Gunicorn（生产级 WSGI 服务器）进行部署。

1. **使用 Gunicorn 运行：**
   ```bash
   uv run gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
   - `-w 4`：使用 4 个工作进程（根据 CPU 核心数调整）。
   - `-b 0.0.0.0:8000`：绑定所有接口的 8000 端口。

2. **反向代理 (Nginx)：**
   建议在 Gunicorn 前面部署 Nginx 来处理静态文件和 SSL。

   Nginx 配置示例片段：
   ```nginx
   server {
       listen 80;
       server_name example.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
       
       client_max_body_size 20M; # 确保此值大于 MAX_CONTENT_LENGTH
   }
   ```

## 项目结构

- `app/`: 应用源代码。
  - `templates/`: HTML 模板。
  - `static/`: 静态资源 (CSS/JS)。
  - `routes.py`: 视图函数和请求处理。
  - `forms.py`: 表单定义和验证。
  - `email_utils.py`: 邮件发送逻辑（含重试和日志）。
  - `config.py`: 配置类。
- `tests/`: 单元测试。
- `uploads/`: 上传文件的临时存储目录。
- `.env`: 环境变量（请勿提交包含机密信息的文件）。

## 安全提示

- 确保生产环境中的 `SECRET_KEY` 是随机且安全的。
- 对 SMTP 连接使用 TLS/SSL (`MAIL_USE_TLS=True`)。
- `MAX_CONTENT_LENGTH` 限制上传大小以防止拒绝服务攻击 (DoS)。
