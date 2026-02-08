# Email Service Application (Backend Focused)

这是一个重构后的邮件发送服务项目，专注于后端逻辑。它移除了一切复杂的前端代码，仅提供一个极简的 API 触发界面。

## 特性

- **极简前端**: 通过单一 API 端点 `/api/simple-frontend` (或根路径 `/`) 渲染，仅包含一个触发按钮。
- **后端核心**: 完整的邮件发送逻辑保留在后端，通过 RESTful API `/api/process-data` 触发。
- **配置化**: 使用环境变量管理 SMTP 和收件人配置。
- **健壮性**: 后端包含自动重试机制和日志记录。

## 快速开始

### 1. 环境准备

确保已安装 Python 3.12+ 和 `uv` (或 pip)。

```bash
git clone <repository-url>
cd EmailApp
uv sync
# 或者手动安装依赖: uv add flask python-dotenv gunicorn
```

### 2. 配置

复制 `.env.example` (如果存在) 或创建 `.env` 文件，并配置 SMTP 信息：

```ini
SECRET_KEY=your-secure-secret-key
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=sender@example.com
MAIL_RECIPIENT=recipient@example.com
```

### 3. 运行服务

启动开发服务器：

```bash
uv run python app.py
```

服务将在 `http://127.0.0.1:5000` 启动。

### 4. 使用方法

#### 方法一：浏览器访问 (极简前端)

在浏览器中打开 `http://127.0.0.1:5000`。
你将看到一个包含“触发后端处理”按钮的页面。点击该按钮即可测试邮件发送功能。

#### 方法二：直接调用 API

你可以使用 `curl` 或 Postman 直接调用后端接口：

```bash
curl -X POST http://127.0.0.1:5000/api/process-data
```

成功响应示例：
```json
{
  "message": "后端逻辑执行成功，邮件已发送！"
}
```

## 项目结构

```
EmailApp/
├── app/
│   ├── __init__.py    # Flask 应用工厂
│   ├── config.py      # 配置管理
│   ├── email_utils.py # 核心邮件发送逻辑
│   └── routes.py      # API 路由定义 (含极简前端 HTML)
├── docs/              # 文档
├── tests/             # 测试用例
├── .env               # 环境变量配置
├── app.py             # 开发启动脚本
└── README.md          # 本文档
```

## 开发与学习

此项目结构非常适合学习后端开发：
1. **API 设计**: 查看 `app/routes.py` 学习如何设计 RESTful 接口。
2. **业务逻辑**: 查看 `app/email_utils.py` 了解如何封装 SMTP 操作和重试机制。
3. **配置管理**: 查看 `app/config.py` 学习 Flask 配置的最佳实践。
