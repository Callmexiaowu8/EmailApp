# Email Service Application

A Python-based web service for sending emails with attachments via a user-friendly web interface. Built with Flask and standard Python libraries.

## Features

- **User Interface**: Clean, responsive web form using Bootstrap 5.
- **File Upload**: Supports various file types (PDF, Images, Docs) up to 16MB.
- **Email Sending**: Uses SMTP with automatic retry mechanism (3 attempts) on failure.
- **Logging**: Detailed transaction logs for auditing and debugging.
- **Security**: CSRF protection, secure filename handling, and input validation.
- **Environment Management**: Managed via `uv`.

## Prerequisites

- Python 3.12+
- `uv` package manager

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd EmailApp
   ```

2. **Initialize environment and install dependencies:**
   ```bash
   uv sync
   ```
   Or manually:
   ```bash
   uv init
   uv add flask flask-wtf python-dotenv gunicorn
   ```

3. **Configuration:**
   Copy `.env.example` (or create `.env`) and configure your SMTP settings.
   ```bash
   cp .env .env.local
   ```
   
   Edit `.env`:
   ```ini
   SECRET_KEY=your-secure-secret-key
   MAIL_SERVER=smtp.example.com
   MAIL_PORT=587
   MAIL_USE_TLS=True
   MAIL_USERNAME=your-email@example.com
   MAIL_PASSWORD=your-password
   MAIL_DEFAULT_SENDER=sender@example.com
   MAIL_RECIPIENT=recipient@example.com
   MAX_CONTENT_LENGTH=16777216  # 16MB in bytes
   UPLOAD_FOLDER=uploads
   ```

## Running Locally

Start the development server:

```bash
uv run python app.py
```

Access the application at `http://127.0.0.1:5000`.

## Running Tests

Run the test suite using `pytest`:

```bash
uv run python -m pytest
```

## Deployment

### Using Gunicorn (Recommended for Production)

This application is ready to be served by Gunicorn, a production-grade WSGI server.

1. **Run with Gunicorn:**
   ```bash
   uv run gunicorn -w 4 -b 0.0.0.0:8000 app:app
   ```
   - `-w 4`: Uses 4 worker processes (adjust based on CPU cores).
   - `-b 0.0.0.0:8000`: Binds to port 8000 on all interfaces.

2. **Reverse Proxy (Nginx):**
   It is recommended to place Nginx in front of Gunicorn to handle static files and SSL.

   Example Nginx config snippet:
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
       
       client_max_body_size 20M; # Ensure this is larger than MAX_CONTENT_LENGTH
   }
   ```

## Project Structure

- `app/`: Application source code.
  - `templates/`: HTML templates.
  - `static/`: Static assets (CSS/JS).
  - `routes.py`: View functions and request handling.
  - `forms.py`: Form definitions and validation.
  - `email_utils.py`: Email sending logic with retry and logging.
  - `config.py`: Configuration class.
- `tests/`: Unit tests.
- `uploads/`: Temporary storage for uploaded files.
- `.env`: Environment variables (do not commit secrets).

## Security Notes

- Ensure `SECRET_KEY` is random and secure in production.
- Use TLS/SSL for SMTP connections (`MAIL_USE_TLS=True`).
- `MAX_CONTENT_LENGTH` limits upload size to prevent DoS.
