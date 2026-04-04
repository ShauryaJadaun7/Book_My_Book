from flask import Flask
from .config import config
from .extensions import db, migrate, login_manager, mail, csrf

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)

    # Register blueprints safely handling if they exist or not yet
    blueprints = [
        ('core', 'core', None),
        ('auth', 'auth', '/auth'),
        ('books', 'books', '/books'),
        ('admin', 'admin_bp', '/admin'),
        ('payments', 'payments_bp', '/payments')
    ]
    
    import importlib
    for package, bp_name, url_prefix in blueprints:
        try:
            module = importlib.import_module(f'.{package}', package=__name__)
            blueprint = getattr(module, bp_name)
            if url_prefix:
                app.register_blueprint(blueprint, url_prefix=url_prefix)
            else:
                app.register_blueprint(blueprint)
        except (ImportError, AttributeError) as e:
            print(f"Skipping {package} blueprint registration due to: {e}")

    return app
