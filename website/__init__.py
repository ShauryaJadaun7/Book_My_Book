from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()

from flask_migrate import Migrate
migrate = Migrate()
import os



def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.urandom(24)
    
    # Configuration
    app.config["SECRET_KEY"] = "SECRET_KEY"
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:12345@localhost:5432/BookMyBook"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Define and Create Upload Folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['IMAGES_FOLDER'] = os.path.join(app.root_path, 'static', 'images')

    # Automatically create both folders if they are missing
    for folder in [app.config['UPLOAD_FOLDER'], app.config['IMAGES_FOLDER']]:
        if not os.path.exists(folder):
            os.makedirs(folder)
        
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

    # Initialize Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from .auth import auth
    from .routes import routes

    app.register_blueprint(auth)
    app.register_blueprint(routes)

    return app