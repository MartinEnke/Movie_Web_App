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
    movies = db.relationship('Movie',
                             secondary=user_movies,
                             back_populates='users')

class Movie(db.Model):
    __tablename__ = 'movies'
    id       = db.Column(db.Integer, primary_key=True)
    title    = db.Column(db.String(120), nullable=False)
    director = db.Column(db.String(120))
    year     = db.Column(db.Integer)
    rating   = db.Column(db.Float)
    poster   = db.Column(db.String(255))
    genre    = db.Column(db.String(120))   # new: genre list, comma‑separated

    users = db.relationship('User',
                            secondary=user_movies,
                            back_populates='movies')

    __table_args__ = (
        db.UniqueConstraint('title', 'year', name='uq_movie_title_year'),
    )
