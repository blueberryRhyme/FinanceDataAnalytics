import os
import sys
import time
import multiprocessing
import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add project root to path
SCRIPT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import TestConfig

# Define a test config that disables achievement hooks
class EnhancedTestConfig(TestConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    DISABLE_ACHIEVEMENT_HOOKS = True  # Prevents achievement hooks

# Create a unified app fixture that all tests can use
@pytest.fixture(scope="function", autouse=True)
def app_for_testing():
    """Provides a fresh Flask app with a new database for each test function.
    This is automatically used in ALL tests through autouse=True.
    """
    from app import create_app, db
    app = create_app(EnhancedTestConfig)
    
    with app.app_context():
        # Create all tables for our models
        db.create_all()
        
        # Make the app available for tests
        yield app
        
        # Clean up after the test
        db.session.remove()
        db.drop_all()

# Add a fixture for tests specifically needing an app context
@pytest.fixture(scope="function")
def app_context(app_for_testing):
    """Provides the app context from the app_for_testing fixture."""
    with app_for_testing.app_context() as ctx:
        yield ctx

# Add a fixture for tests specifically needing access to the database
@pytest.fixture(scope="function")
def db(app_for_testing):
    """Provides access to the database from the app_for_testing fixture."""
    from app import db
    return db

# Helper to run app in a separate process for selenium tests
def run_app():
    from run import app
    app.run(port=5000, use_reloader=False)

# Flask server for end-to-end tests (not auto-used)
@pytest.fixture(scope="session")
def flask_server():
    proc = multiprocessing.Process(target=run_app)
    proc.daemon = True
    proc.start()
    time.sleep(2)
    yield
    proc.terminate()
    proc.join(timeout=5)