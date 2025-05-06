from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize db globally
db = SQLAlchemy()


def create_app():
    """Factory function to create and configure the Flask app"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_web.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db with the app only once
    db.init_app(app)

    # Import routes and other modules
    with app.app_context():
        from Movie_Web_App.data_manager.sqlite_data_manager import SQLiteDataManager
        from Movie_Web_App.data_manager.models import User, Movie

        # Initialize SQLiteDataManager
        data_manager = SQLiteDataManager(db)

    return app
