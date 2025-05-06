from Movie_Web_App import db  # Import db from the global app context

# Define the models here
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    movies = db.relationship('Movie', backref='user', lazy=True)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    director = db.Column(db.String(120))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
