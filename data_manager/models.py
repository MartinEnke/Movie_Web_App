from datetime import datetime
from Movie_Web_App import db


# Association table for users↔movies
user_movies = db.Table(
    'user_movies',
    db.Column('user_id',  db.Integer, db.ForeignKey('users.id'),   primary_key=True),
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'),  primary_key=True),
    db.Column('added_at', db.DateTime, default=datetime.utcnow)
)

class User(db.Model):
    __tablename__ = 'users'
    id     = db.Column(db.Integer, primary_key=True)
    name   = db.Column(db.String(80), unique=True, nullable=False)

    # Many-to-many to Movie
    movies = db.relationship('Movie', secondary=user_movies, back_populates='users')
    reviews = db.relationship('Review', back_populates='user', cascade="all, delete-orphan")


class Movie(db.Model):
    __tablename__ = 'movies'
    id       = db.Column(db.Integer, primary_key=True)
    title    = db.Column(db.String(120), nullable=False)
    director = db.Column(db.String(120))
    year     = db.Column(db.Integer)
    rating   = db.Column(db.Float)
    poster   = db.Column(db.String(255))
    genre    = db.Column(db.String(120))   # new: genre list, comma‑separated
    plot     = db.Column(db.Text, nullable=True)

    users = db.relationship('User', secondary=user_movies, back_populates='movies')
    reviews = db.relationship('Review', back_populates='movie', cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('title', 'year', name='uq_movie_title_year'),
    )


class Review(db.Model):
    __tablename__ = "reviews"

    review_id   = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    movie_id    = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    rating      = db.Column(db.Float, nullable=False)
    created_at  = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # relationships
    user  = db.relationship('User', back_populates='reviews')
    movie = db.relationship('Movie', back_populates='reviews')
