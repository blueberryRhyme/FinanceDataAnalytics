import os
from flask import Flask
from flask_wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    
    app.config.from_object('config.Config')
    
    #   cross site request forgery
    CSRFProtect(app)
    
    db.init_app(app)
    migrate.init_app(app, db) 
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Import User model here to avoid circular imports
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        #   Flask-Login passes the user ID as a string ?
        return User.query.get(int(user_id))


    # import here to avoid circular import
    from .routes import main
    app.register_blueprint(main)
        
    return app
