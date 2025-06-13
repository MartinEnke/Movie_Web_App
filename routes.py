from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort, current_app
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_

from . import db, data_manager
from .data_manager.models import User, Movie
from .omdb_api import fetch_movie_data

main = Blueprint('main', __name__)

@main.errorhandler(404)
def page_not_found(error):
    """
    Render custom 404 page.
    """
    return render_template('404.html'), 404

@main.errorhandler(500)
def internal_error(error):
    """
    Handle internal server errors by rolling back the session
    and rendering a 500 page.
    """
    db.session.rollback()
    return render_template('500.html'), 500

@main.route('/')
def index():
    """
    Home page: list all movies, with optional search and genre filter.
    """
    q = request.args.get('q', '').strip()
    sel_genre = request.args.get('genre', '').strip()

    # Build base query
    query = Movie.query
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(Movie.title.ilike(pattern), Movie.director.ilike(pattern))
        )
    if sel_genre:
        query = query.filter(Movie.genre.ilike(f"%{sel_genre}%"))

    try:
        movies = query.all()
    except SQLAlchemyError:
        current_app.logger.exception("DB error on index")
        abort(500)

    # Flash messages if no results
    if not movies:
        if q or sel_genre:
            msg = "No matches for "
            if q:
                msg += f"“{q}” "
            if sel_genre:
                msg += f"in genre “{sel_genre}”"
            flash(msg, "warning")
        else:
            flash("No movies yet—why not seed the catalog?", "info")

    # Build genre list for dropdown
    raw_genres = Movie.query.with_entities(Movie.genre).filter(Movie.genre.isnot(None)).all()
    genre_set = {g.strip() for (row,) in raw_genres for g in (row or '').split(',') if g.strip()}
    genres = sorted(genre_set)

    return render_template(
        'index.html', movies=movies,
        query=q, selected_genre=sel_genre,
        genres=genres
    )

@main.route('/add_user', methods=['GET', 'POST'])
def add_user():
    """
    Add a new user to the database.
    """
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash("Enter a name.", "warning")
        elif len(name) < 3:
            flash("Name too short.", "warning")
        else:
            user = User(name=name)
            db.session.add(user)
            try:
                db.session.commit()
                flash(f"User “{user.name}” created.", "success")
                return redirect(url_for('main.list_users'))
            except IntegrityError:
                db.session.rollback()
                flash(f"A user named '{name}' already exists.", "error")
            except SQLAlchemyError:
                db.session.rollback()
                current_app.logger.exception("DB error creating user")
                abort(500)
    return render_template('add_user.html')

@main.route('/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """
    Remove a user (and all their movie‐list associations & reviews) from the system.
    """
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"Deleted user “{user.name}”.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("DB error deleting user")
        flash("Could not delete user. Try again.", "error")
    return redirect(url_for('main.list_users'))

@main.route('/users')
def list_users():
    """
    List all users.
    """
    try:
        users = User.query.all() or []
    except SQLAlchemyError:
        current_app.logger.exception("DB error listing users")
        abort(500)
    if not users:
        flash("No users found.", "info")
    return render_template('users_list.html', users=users)

@main.route('/users/<int:user_id>')
def user_movies(user_id):
    """
    Display a user's movie list with optional catalog search.
    Tries OMDb if no local movie matches are found.
    """
    user = User.query.get_or_404(user_id)
    q = request.args.get('q', '').strip()
    new_results, owned_results = [], []

    if q:
        catalog = Movie.query.filter(
            or_(Movie.title.ilike(f'%{q}%'), Movie.director.ilike(f'%{q}%'))
        ).all()

        owned_ids = {m.id for m in user.movies}
        for m in catalog:
            (owned_results if m.id in owned_ids else new_results).append(m)

        # ✅ OMDb fallback if no DB matches
        if not catalog:
            try:
                data = fetch_movie_data(q)
                if data:
                    movie = Movie(**data)
                    db.session.add(movie)
                    db.session.commit()
                    new_results.append(movie)
                    flash(f"Fetched “{movie.title}” from OMDb.", "info")
                else:
                    flash("No movie found via OMDb.", "warning")
            except Exception:
                db.session.rollback()
                current_app.logger.exception("OMDb error in user_movies")
                flash("Could not fetch movie from OMDb.", "error")

    return render_template(
        'user_movies.html', user=user,
        movies=user.movies, query=q,
        new_results=new_results, owned_results=owned_results
    )


@main.route('/users/<int:user_id>/add_existing/<movie_id>', methods=['POST'])
def add_existing_movie(user_id, movie_id):
    """
    Add a movie to a user's list. If movie_id is numeric, use local DB;
    if not, treat as title and fetch from OMDb if not in DB.
    """
    user = User.query.get_or_404(user_id)
    q = request.form.get('q', '').strip()

    try:
        # Try interpreting as a local movie ID
        movie_id_int = int(movie_id)
        movie = Movie.query.get_or_404(movie_id_int)

        if movie in user.movies:
            flash(f"“{movie.title}” is already in your list.", "warning")
        else:
            user.movies.append(movie)
            db.session.commit()
            flash(f"Added “{movie.title}” to your list!", "success")

    except ValueError:
        # Not an int? Treat as title and try to find it locally
        title = movie_id.strip()
        movie = Movie.query.filter(Movie.title.ilike(title)).first()

        if movie and movie in user.movies:
            flash(f"“{movie.title}” is already in your list.", "warning")
        else:
            # Fetch from OMDb if not found
            if not movie:
                try:
                    data = fetch_movie_data(title)
                    if not data:
                        flash("Movie not found via OMDb.", "warning")
                        return redirect(url_for('main.user_movies', user_id=user_id, q=q))
                    movie = Movie(**data)
                    db.session.add(movie)
                except Exception:
                    db.session.rollback()
                    current_app.logger.exception("OMDb or DB error")
                    flash("Could not fetch movie.", "error")
                    return redirect(url_for('main.user_movies', user_id=user_id, q=q))

            user.movies.append(movie)
            try:
                db.session.commit()
                flash(f"Added “{movie.title}” to your list (via OMDb)!", "success")
            except SQLAlchemyError:
                db.session.rollback()
                flash("Could not save movie.", "error")

    # Redirect preserving search if needed
    if q:
        remaining = [m for m in Movie.query.filter(
            or_(Movie.title.ilike(f'%{q}%'), Movie.director.ilike(f'%{q}%'))
        ).all() if m.id not in {mv.id for mv in user.movies}]
        if remaining:
            return redirect(url_for('main.user_movies', user_id=user_id, q=q))

    return redirect(url_for('main.user_movies', user_id=user_id))


@main.route('/users/<int:user_id>/add_movie', methods=['GET', 'POST'])
def add_movie(user_id):
    """
    Fetch via OMDb and add new movie to global catalog and user's list.
    """
    if request.method == 'POST':
        title = request.form.get('name', '').strip()
        if not title:
            flash("Enter a movie title.", "warning")
        else:
            try:
                data = fetch_movie_data(title)
            except Exception:
                current_app.logger.exception("OMDb error")
                flash("OMDb unreachable.", "error")
                return render_template('add_movie.html', user_id=user_id)
            if not data:
                flash("Movie not found.", "warning")
            else:
                movie = Movie(**data)
                db.session.add(movie)
                try:
                    db.session.commit()
                    flash(f"“{movie.title}” added.", "success")
                    return redirect(url_for('main.user_movies', user_id=user_id))
                except SQLAlchemyError:
                    db.session.rollback()
                    current_app.logger.exception("DB error adding movie")
                    flash("Error saving movie.", "error")
    return render_template('add_movie.html', user_id=user_id)


@main.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    """
    Edit a movie's details.
    """
    movie = Movie.query.get_or_404(movie_id)
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        movie.title = request.form['name'].strip()
        movie.director = request.form['director'].strip()
        movie.year = request.form['year'].strip()
        movie.rating = request.form['rating'].strip()
        db.session.commit()

        flash("Movie updated successfully.", "success")
        return redirect(url_for('main.user_movies', user_id=user_id))

    return render_template('update_movie.html', movie=movie, user=user)


@main.route('/users/<int:user_id>/remove_movie/<int:movie_id>', methods=['POST'])
def remove_movie(user_id, movie_id):
    """
    Remove the association between user and movie.
    """
    user = User.query.get_or_404(user_id)
    movie = Movie.query.get_or_404(movie_id)
    if movie not in user.movies:
        abort(404)
    try:
        user.movies.remove(movie)
        db.session.commit()
        flash(f"Removed '{movie.title}' from your list.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("DB error removing movie from user")
        flash("Could not remove movie. Try again.", "error")
    return redirect(url_for('main.user_movies', user_id=user_id))

@main.route('/search')
def search():
    """
    Global search for users and movies by name or title/director.
    If no movie is found locally, try fetching from OMDb.
    """
    q = request.args.get('q', '').strip()
    if not q:
        return render_template('search_results.html', query=q, users=[], movies=[])

    try:
        # Search local DB
        users = User.query.filter(User.name.ilike(f"%{q}%")).all()
        movies = Movie.query.filter(
            or_(Movie.title.ilike(f"%{q}%"), Movie.director.ilike(f"%{q}%"))
        ).all()

        # If no local movie found, try OMDb fetch
        if not movies:
            try:
                data = fetch_movie_data(q)
                if data:
                    movie = Movie(**data)
                    db.session.add(movie)
                    db.session.commit()
                    movies = [movie]
                    flash(f"Fetched “{movie.title}” from OMDb.", "info")
                else:
                    flash("No movies found matching your search.", "warning")
            except Exception:
                db.session.rollback()
                current_app.logger.exception("OMDb error during search")
                flash("Could not reach OMDb for movie search.", "error")

    except SQLAlchemyError:
        current_app.logger.exception("DB error during search")
        users = movies = []
        flash("An error occurred while searching.", "error")

    return render_template('search_results.html', query=q, users=users, movies=movies)



@main.route('/movies/<int:movie_id>', methods=['GET', 'POST'])
def movie_detail(movie_id):
    """
    Show details and reviews for a movie; allow posting a review.
    """
    movie = Movie.query.get_or_404(movie_id)
    reviews = data_manager.get_movie_reviews(movie_id)
    if request.method == 'POST':
        text = request.form['review_text']
        rating = float(request.form['rating'])
        try:
            data_manager.add_review(movie_id=movie_id, review_text=text, rating=rating)
            flash("Review added!", "success")
            return redirect(url_for('main.movie_detail', movie_id=movie_id))
        except Exception:
            current_app.logger.exception("Failed to save review")
            flash("Could not save your review—please try again.", "error")
    return render_template('movie_detail.html', movie=movie, reviews=reviews)
