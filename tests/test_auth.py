import pytest
from unittest.mock import patch


def register_user(client, username="u1", password="p1"):
    return client.post(
        "/register",
        data={"username": username, "password": password, "confirm_password": password},
        follow_redirects=True,
    )


def login_user(client, username="u1", password="p1"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_email_settings_requires_login(client):
    response = client.get("/settings/email")
    assert response.status_code in (301, 302)
    assert "/login" in response.headers.get("Location", "")


def test_register_and_login_flow(client):
    response = register_user(client, username="alice", password="secret")
    assert response.status_code == 200
    assert b"Send Email" in response.data
    assert b"alice" in response.data

    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200

    response = login_user(client, username="alice", password="secret")
    assert response.status_code == 200
    assert b"alice" in response.data


@patch("app.email_utils.smtplib.SMTP")
def test_send_email_uses_user_email_account(mock_smtp, client, app):
    instance = mock_smtp.return_value
    instance.sendmail.return_value = {}

    register_user(client, username="bob", password="secret")

    response = client.post(
        "/settings/email",
        data={
            "email": "bob@example.com",
            "smtp_server": "smtp.example.com",
            "smtp_port": "2525",
            "auth_code": "app-password",
            "use_tls": "on",
            "is_default": "on",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "保存成功".encode("utf-8") in response.data

    app.config["MAIL_SERVER"] = "localhost"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = False
    app.config["MAIL_USERNAME"] = "x"
    app.config["MAIL_PASSWORD"] = "y"
    app.config["MAIL_DEFAULT_SENDER"] = "sender@example.com"

    response = client.post(
        "/",
        data={"recipient": "to@example.com", "content": "hello"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Email sent successfully!" in response.data

    mock_smtp.assert_called_once_with("smtp.example.com", 2525)
    instance.starttls.assert_called_once()
    instance.login.assert_called_once_with("bob@example.com", "app-password")
    instance.sendmail.assert_called_once()
