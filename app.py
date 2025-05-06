from flask import render_template, request, redirect, url_for
from Movie_Web_App import create_app, db, data_manager  # Import the factory and db object
from Movie_Web_App.data_manager.models import User, Movie
from Movie_Web_App.data_manager.sqlite_data_manager import SQLiteDataManager
import requests

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
    if request.method == 'POST':
        # Get movie details from the form
        name = request.form['name']
        director = request.form['director']
        year = request.form['year']
        rating = request.form['rating']

        # Optionally, you can fetch movie details from OMDb API (if needed)
        omdb_url = f"http://www.omdbapi.com/?t={name}&apikey=your_api_key"
        omdb_response = requests.get(omdb_url)
        movie_data = omdb_response.json()

        # Use the OMDb data to populate the movie fields (e.g., year, rating)
        year = movie_data.get('Year', year)
        rating = movie_data.get('imdbRating', rating)

        # Add movie to the database
        data_manager.add_movie(name, director, year, rating, user_id)

        # Redirect to the user's movie list
        return redirect(url_for('user_movies', user_id=user_id))

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
    #with app.app_context():
        # db.drop_all()  # Drops all tables in the database
        # db.create_all()  # Creates the tables again based on models
        # print("Tables created successfully!")
    app.run(port=5030, debug=True)
