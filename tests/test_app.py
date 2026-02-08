import pytest
from unittest.mock import patch, MagicMock
import os
from io import BytesIO

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Send Email" in response.data

@patch('app.email_utils.smtplib.SMTP')
def test_send_email_success(mock_smtp, client, app):
    # Mock SMTP instance
    instance = mock_smtp.return_value
    instance.sendmail.return_value = {}
    
    data = {
        'content': 'Test Message',
    }
    
    # We need to configure MAIL settings in app config for the test
    app.config['MAIL_SERVER'] = 'localhost'
    app.config['MAIL_DEFAULT_SENDER'] = 'sender@example.com'
    app.config['MAIL_RECIPIENT'] = 'recipient@example.com'
    app.config['MAIL_USERNAME'] = 'user'
    app.config['MAIL_PASSWORD'] = 'pass'

    response = client.post('/', data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Email sent successfully!" in response.data
    instance.sendmail.assert_called_once()

@patch('app.email_utils.smtplib.SMTP')
def test_send_email_with_file(mock_smtp, client, app):
    instance = mock_smtp.return_value
    
    data = {
        'content': 'Test Message with File',
        'file': (BytesIO(b"file content"), 'test.txt')
    }
    
    app.config['MAIL_SERVER'] = 'localhost'
    app.config['MAIL_DEFAULT_SENDER'] = 'sender@example.com'
    app.config['MAIL_RECIPIENT'] = 'recipient@example.com'
    app.config['MAIL_USERNAME'] = 'user'
    app.config['MAIL_PASSWORD'] = 'pass'

    response = client.post('/', data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Email sent successfully!" in response.data
    instance.sendmail.assert_called_once()

@patch('app.email_utils.smtplib.SMTP')
def test_send_email_retry_failure(mock_smtp, client, app):
    # Simulate exception
    mock_smtp.side_effect = Exception("Connection refused")
    
    data = {
        'content': 'Test Fail',
    }
    
    app.config['MAIL_SERVER'] = 'localhost'
    app.config['MAIL_DEFAULT_SENDER'] = 'sender@example.com'
    app.config['MAIL_RECIPIENT'] = 'recipient@example.com'

    # Speed up sleep
    with patch('time.sleep', return_value=None):
        response = client.post('/', data=data, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Failed to send email" in response.data
    assert mock_smtp.call_count == 3 # 3 retries
