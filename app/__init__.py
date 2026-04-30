import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # required for google oauth over http in development
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access Data-Forge."
    login_manager.login_message_category = "warning"

    from app.routes import main
    from app.auth import auth
    from app.google_auth import google_auth

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(google_auth)

    return app
    