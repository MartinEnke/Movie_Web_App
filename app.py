from flask import render_template, request, redirect, url_for
from Movie_Web_App import create_app, db, data_manager  # Import the factory and db object
from Movie_Web_App.data_manager.models import User, Movie
from Movie_Web_App.data_manager.sqlite_data_manager import SQLiteDataManager
import requests
from Movie_Web_App.omdb_api import fetch_movie_data  # Import your custom OMDb module

# Create the Flask app using the factory
app = create_app()
# initializing the data_manager
data_manager = SQLiteDataManager(db)


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

        # Add the new user using the DataManager
        data_manager.add_user(name)

        # Redirect to the list of users
        return redirect(url_for('list_users'))

    return render_template('add_user.html')

@app.route('/users/<int:user_id>')
def user_movies(user_id):
    # Fetch the user and their movies
    user = User.query.get_or_404(user_id)  # Get the user by ID, or return 404 if not found
    movies = data_manager.get_user_movies(user_id)  # Use the DataManager to get user's movies

    return render_template('user_movies.html', user=user, movies=movies)


@app.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    movie_details = None  # Default value for movie details

    if request.method == 'POST':
        # Get the movie title from the form
        name = request.form['name']
        director = request.form['director']
        year = request.form['year']
        rating = request.form['rating']
        # Ensure 'poster' is handled properly even if it's missing in the form
        poster = request.form.get('poster', '')  # Default to an empty string if 'poster' is missing

        # If the name is provided, fetch movie data from OMDb API
        if name:
            # Fetch movie data from OMDb using the custom function
            movie_data = fetch_movie_data(name)

            if movie_data:  # If data was fetched from OMDb
                # Fill missing data with OMDb API response
                year = movie_data['year']
                rating = movie_data['rating']
                poster = movie_data['poster']  # Use the poster from OMDb response

                # Handle missing or unavailable director information
                director = movie_data['director'] if movie_data['director'] != "N/A" else director

            else:
                # Handle the case where the movie was not found in OMDb
                movie_details = {"error": "Movie not found in OMDb database"}

        # Add the movie to the database (poster is now used correctly)
        new_movie = Movie(name=name, director=director, year=year, rating=rating, user_id=user_id, poster=poster)
        db.session.add(new_movie)
        db.session.commit()

        # Redirect to the user's movie list
        return redirect(url_for('user_movies', user_id=user_id))

    return render_template('add_movie.html', user_id=user_id, movie_details=movie_details)



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
