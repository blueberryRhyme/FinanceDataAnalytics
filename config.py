import os
class Config:
    SECRET_KEY =  os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig:
    TESTING = True
    SECRET_KEY = os.environ.get('TEST_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
