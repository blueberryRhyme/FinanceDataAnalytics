import os
from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade as alembic_upgrade
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_object=None):
    app = Flask(__name__)
    
    if config_object:
        app.config.from_object(config_object)
    else:
        app.config.from_pyfile('../config.py')
    
    
    #   cross site request forgery
    CSRFProtect(app)
    
    db.init_app(app)
    migrate.init_app(app, db) 
    login_manager.init_app(app)
    

    # Import User model here to avoid circular imports
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        #   Flask-Login passes the user ID as a string ?
        from app.models import db, User

        return db.session.get(User, int(user_id))


    # import here to avoid circular import
    from .routes import main
    app.register_blueprint(main)
        
    return app