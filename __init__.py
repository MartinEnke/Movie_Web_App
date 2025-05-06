from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/martinenke/Movie_Web_App/movie_web.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize db with the app
    db.init_app(app)

    # Import routes, models, etc.
    with app.app_context():
        from Movie_Web_App.data_manager.sqlite_data_manager import SQLiteDataManager
        from Movie_Web_App.data_manager.models import User, Movie
        data_manager = SQLiteDataManager(db)

    return app
