import pytest
from app import create_app
from app.config import Config
import os
import shutil

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = 'tests/uploads'

@pytest.fixture
def app():
    if not os.path.exists('tests/uploads'):
        os.makedirs('tests/uploads')
    
    app = create_app(TestConfig)
    
    yield app
    
    # Cleanup
    if os.path.exists('tests/uploads'):
        shutil.rmtree('tests/uploads')

@pytest.fixture
def client(app):
    return app.test_client()
