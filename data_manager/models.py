from Movie_Web_App import db  # Import db from the global app context


# Define the User model
class User(db.Model):
    __tablename__ = "users"  # Define the table name

    # Columns
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the User model
    name = db.Column(db.String(80), unique=True, nullable=False)  # User's name, must be unique

    # Relationship to Movie
    movies = db.relationship('Movie', backref='user', lazy=True)  # Relationship to Movie, with a backref to 'user'


# Define the Movie model
class Movie(db.Model):
    __tablename__ = "movies"  # Define the table name

    # Columns
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the Movie model
    name = db.Column(db.String(120), nullable=False)  # Movie name
    director = db.Column(db.String(120))  # Movie director
    year = db.Column(db.Integer)  # Release year
    rating = db.Column(db.Float)  # Movie rating

    # Foreign key to the User table
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        nullable=False)  # Reference to the user who owns the movie

