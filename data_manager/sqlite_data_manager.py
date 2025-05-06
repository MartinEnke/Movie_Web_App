from Movie_Web_App.data_manager.data_manager_interface import DataManagerInterface
from Movie_Web_App.data_manager.models import Movie, User

class SQLiteDataManager(DataManagerInterface):
    def __init__(self, db):
        """Initialize with the db object from the Flask app"""
        self.db = db

    def get_all_users(self):
        """Fetch all users from the database"""
        return User.query.all()  # Return all users using SQLAlchemy ORM

    def get_user_movies(self, user_id):
        """Fetch movies for a specific user"""
        return Movie.query.filter_by(user_id=user_id).all()

    def add_user(self, name):
        """Add a new user to the database"""
        new_user = User(name=name)
        self.db.session.add(new_user)
        self.db.session.commit()

    def add_movie(self, name, director, year, rating, user_id):
        """Add a new movie for a user"""
        new_movie = Movie(name=name, director=director, year=year, rating=rating, user_id=user_id)
        self.db.session.add(new_movie)
        self.db.session.commit()

    def update_movie(self, movie_id, name, director, year, rating):
        """Update movie details"""
        movie = Movie.query.get(movie_id)
        if movie:
            movie.name = name
            movie.director = director
            movie.year = year
            movie.rating = rating
            self.db.session.commit()

    def delete_movie(self, movie_id):
        """Delete a movie"""
        movie = Movie.query.get(movie_id)
        if movie:
            self.db.session.delete(movie)
            self.db.session.commit()
