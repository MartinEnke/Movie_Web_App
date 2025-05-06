from flask import render_template, request, redirect, url_for
from Movie_Web_App import create_app, db, data_manager  # Import the factory and db object
from Movie_Web_App.data_manager.models import User, Movie
from Movie_Web_App.data_manager.sqlite_data_manager import SQLiteDataManager

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

@app.route('/user/<int:user_id>')
def user_movies(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('user_movies.html', user=user)

@app.route('/add_movie/<int:user_id>', methods=['GET', 'POST'])
def add_movie(user_id):
    if request.method == 'POST':
        name = request.form['name']
        director = request.form['director']
        year = request.form['year']
        rating = request.form['rating']
        movie = Movie(name=name, director=director, year=year, rating=rating, user_id=user_id)
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('user_movies', user_id=user_id))
    return render_template('add_movie.html', user_id=user_id)

@app.route('/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        movie.name = request.form['name']
        movie.director = request.form['director']
        movie.year = request.form['year']
        movie.rating = request.form['rating']
        db.session.commit()
        return redirect(url_for('user_movies', user_id=movie.user_id))
    return render_template('update_movie.html', movie=movie)

@app.route('/delete_movie/<int:movie_id>')
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('user_movies', user_id=movie.user_id))



if __name__ == '__main__':
    # Create tables
    with app.app_context():
        db.drop_all()  # Drops all tables in the database
        db.create_all()  # Creates the tables again based on models
        print("Tables created successfully!")
    app.run(port=5030, debug=True)
