import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize the SQLAlchemy object
db = SQLAlchemy()
data_manager = None

# Application factory
def create_app(test_config: dict = None):
    app = Flask(__name__, instance_relative_config=True)

    # Default production config
    app.config.from_mapping(
        SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key'),
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(app.instance_path, 'movie_web.db')}",
        SQLALCHEMY_TRACK_MODIFICATIONS = False,
    )

    # Override with testing config if provided
    if test_config:
        app.config.update(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Initialize extensions
    db.init_app(app)

    # Bind data manager after db is initialized
    from .data_manager.sqlite_data_manager import SQLiteDataManager
    global data_manager
    data_manager = SQLiteDataManager(db)
    # Also attach to app so blueprints can access
    app.data_manager = data_manager

    # Register blueprints
    from .routes import main
    app.register_blueprint(main)

    return app