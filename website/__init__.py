from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


db = SQLAlchemy()

from flask_migrate import Migrate
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    migrate = Migrate(app, db)

    migrate.init_app(app, db)

    app.config["SECRET_KEY"] = "SECRET_KEY"
    app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:12345@localhost:5432/BookMyBook"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    login_manager = LoginManager()

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth import auth
    from .routes import routes

    app.register_blueprint(auth)
    app.register_blueprint(routes)

    return app
