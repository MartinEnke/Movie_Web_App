from flask import render_template, request, redirect, url_for, abort, flash, current_app
from Movie_Web_App import create_app, db, data_manager  # Import the factory and db object
from Movie_Web_App.data_manager.models import User, Movie
from Movie_Web_App.data_manager.sqlite_data_manager import SQLiteDataManager
import requests
from Movie_Web_App.omdb_api import fetch_movie_data  # Import your custom OMDb module
import os

# Create the Flask app using the factory
app = create_app()

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# initializing the data_manager
data_manager = SQLiteDataManager(db)


# error routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    # optional: roll back DB session if you’re using SQLAlchemy
    db.session.rollback()
    return render_template('500.html'), 500


# Define routes
@app.route('/')
def index():
    users = db.session.query(User).all()
    return render_template('index.html', users=users)

@app.route('/home')
def home():
    return "Welcome to MovieWeb App!"

@app.route('/users')
def list_users():
    users = data_manager.get_all_users()  # Call the method from data_manager
    return render_template('users_list.html', users=users)  # Pass users to a template

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # Get the name from the form
        name = request.form['name']
        if len(name) < 3:
            return "Name too short", 400

        # Add the new user using the DataManager
        data_manager.add_user(name)

        # Redirect to the list of users
        return redirect(url_for('list_users'))

    return render_template('add_user.html')

@app.route('/users/<int:user_id>')
def user_movies(user_id):
    # Fetch the user and their movies
    user = User.query.get_or_404(user_id)  # Get the user by ID, or return 404 if not found
    if user is None:
        abort(404)
    movies = data_manager.get_user_movies(user_id)  # Use the DataManager to get user's movies

    return render_template('user_movies.html', user=user, movies=movies)


@app.route('/users/<int:user_id>/add_movie', methods=['GET','POST'])
def add_movie(user_id):
    if request.method == 'POST':
        title = request.form.get('name','').strip()
        if not title:
            flash("Please enter a movie title.", "warning")
            return render_template('add_movie.html', user_id=user_id)

        # 1) Fetch from OMDb
        try:
            movie_data = fetch_movie_data(title)
        except Exception:
            current_app.logger.exception("OMDb lookup failed")
            flash("Could not reach OMDb. Try again later.", "error")
            return render_template('add_movie.html', user_id=user_id)

        if not movie_data:
            flash("Movie not found in OMDb.", "warning")
            return render_template('add_movie.html', user_id=user_id)

        # 2) Build the Movie using fetched data (fall back to form fields only if OMDb field is missing)
        director = (movie_data['director']
                    if movie_data['director'] != "N/A"
                    else request.form.get('director','').strip())
        year    = movie_data.get('year')   or request.form.get('year','').strip()
        rating  = movie_data.get('rating') or request.form.get('rating','').strip()
        poster  = movie_data.get('poster') or request.form.get('poster','').strip()

        new_movie = Movie(
            name=title,
            director=director,
            year=year,
            rating=rating,
            poster=poster,
            user_id=user_id
        )

        # 3) Commit & redirect
        try:
            db.session.add(new_movie)
            db.session.commit()
            flash(f"“{title}” added to your list!", "success")
            return redirect(url_for('user_movies', user_id=user_id))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Database error adding movie")
            flash("Error saving movie. Please try again.", "error")
            return render_template('add_movie.html', user_id=user_id)

    # GET
    return render_template('add_movie.html', user_id=user_id)


@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    movie = Movie.query.get_or_404(movie_id)  # Get the movie by ID
    user = User.query.get_or_404(user_id)  # Get the user by ID

    if request.method == 'POST':
        # Get the updated movie details from the form
        movie.name = request.form['name']
        movie.director = request.form['director']
        movie.year = request.form['year']
        movie.rating = request.form['rating']

        # Commit changes to the database
        db.session.commit()

        # Redirect to the user's movie list
        return redirect(url_for('user_movies', user_id=user_id))

    return render_template('update_movie.html', user=user, movie=movie)


@app.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['GET', 'POST'])
def delete_movie(user_id, movie_id):
    movie = Movie.query.get_or_404(movie_id)  # Get the movie by ID
    db.session.delete(movie)  # Delete the movie
    db.session.commit()  # Commit the deletion to the database

    return redirect(url_for('user_movies', user_id=user_id))


if __name__ == '__main__':
    # Create tables
    # with app.app_context():
    #     db.drop_all()  # Drops all tables in the database
    #     db.create_all()  # Creates the tables again based on models
    #     print("Tables created successfully!")
    app.run(port=5030, debug=True)
