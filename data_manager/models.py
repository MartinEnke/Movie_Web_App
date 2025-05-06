from Movie_Web_App import db  # Import db from the global app context


# Define the User model
class User(db.Model):
    __tablename__ = "users"  # Define the table name

    # Columns
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the User model
    name = db.Column(db.String(80), unique=True, nullable=False)  # User's name, must be unique

    # Relationship to Movie
    movies = db.relationship('Movie', backref='owner', lazy=True)  # Change 'user' to 'owner'


# Define the Movie model
class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    director = db.Column(db.String(120))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    poster = db.Column(db.String(255))

    # Relationship to User
    user = db.relationship('User', backref='movies_owned', lazy=True)  # Updated backref to 'movies_owned'

