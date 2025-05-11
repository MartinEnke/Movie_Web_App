from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort, current_app
)
from . import db, data_manager
from .data_manager.models import User, Movie
from .omdb_api import fetch_movie_data
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_

main = Blueprint('main', __name__)

@main.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

@main.route('/')
def index():
    try:
        movies = Movie.query.order_by(Movie.title).all()
    except SQLAlchemyError:
        current_app.logger.exception("DB error on index")
        abort(500)

    if not movies:
        flash("No movies in the catalog yet—seed some with `flask seed-movies`!", "info")

    return render_template('index.html', movies=movies)

@main.route('/add_user', methods=['GET','POST'])
def add_user():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        if not name:
            flash("Enter a name.", "warning")
            return render_template('add_user.html')
        if len(name) < 3:
            flash("Name too short.", "warning")
            return render_template('add_user.html')

        user = User(name=name)
        db.session.add(user)
        try:
            db.session.commit()
            flash(f"User “{user.name}” created.", "success")
            return redirect(url_for('main.list_users'))
        except IntegrityError:
            db.session.rollback()
            flash(f"A user named '{name}' already exists.", "error")
            return render_template('add_user.html')
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("DB error creating user")
            abort(500)

    return render_template('add_user.html')

@main.route('/users')
def list_users():
    try:
        users = User.query.all() or []
    except SQLAlchemyError:
        current_app.logger.exception("DB error listing users")
        abort(500)

    if not users:
        flash("No users found.", "info")
    return render_template('users_list.html', users=users)


@main.route('/users/<int:user_id>', methods=['GET'])
def user_movies(user_id):
    user = User.query.get_or_404(user_id)
    q    = request.args.get('q', '').strip()

    # Prepare two result‐sets
    new_results   = []
    owned_results = []

    if q:
        # Search the global catalog
        catalog = Movie.query.filter(
            (Movie.title.ilike(f'%{q}%')) |
            (Movie.director.ilike(f'%{q}%'))
        ).all()

        # Partition into owned vs new
        owned_ids = {m.id for m in user.movies}
        for m in catalog:
            if m.id in owned_ids:
                owned_results.append(m)
            else:
                new_results.append(m)

    return render_template(
        'user_movies.html',
        user=user,
        movies=user.movies,
        query=q,
        new_results=new_results,
        owned_results=owned_results
    )


@main.route('/users/<int:user_id>/add_existing/<int:movie_id>', methods=['POST'])
def add_existing_movie(user_id, movie_id):
    user  = User.query.get_or_404(user_id)
    movie = Movie.query.get_or_404(movie_id)

    # grab q from the form (we’ll include it below)
    q = request.form.get('q','').strip()

    if movie in user.movies:
        flash(f"“{movie.title}” is already in your list.", "warning")
    else:
        try:
            user.movies.append(movie)
            db.session.commit()
            flash(f"Added “{movie.title}” to your list!", "success")
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("DB error attaching movie")
            flash("Could not add movie. Try again.", "error")

    # now recompute how many new matches remain for this q
    remaining = []
    if q:
        catalog = Movie.query.filter(
            (Movie.title.ilike(f'%{q}%')) |
            (Movie.director.ilike(f'%{q}%'))
        ).all()
        owned_ids = {m.id for m in user.movies}
        remaining = [m for m in catalog if m.id not in owned_ids]

    # if we still have unmatched results, keep the q in the URL
    if q and remaining:
        return redirect(url_for('main.user_movies', user_id=user_id, q=q))
    # otherwise clear the search
    return redirect(url_for('main.user_movies', user_id=user_id))



@main.route('/users/<int:user_id>/add_movie', methods=['GET','POST'])
def add_movie(user_id):
    if request.method == 'POST':
        title = request.form.get('name','').strip()
        if not title:
            flash("Enter a movie title.", "warning")
            return render_template('add_movie.html', user_id=user_id)

        try:
            data = fetch_movie_data(title)
        except Exception:
            current_app.logger.exception("OMDb error")
            flash("OMDb unreachable.", "error")
            return render_template('add_movie.html', user_id=user_id)

        if not data:
            flash("Movie not found.", "warning")
            return render_template('add_movie.html', user_id=user_id)

        # Parse a single year from OMDb’s Year (handles ranges and ints)
        raw_year = data.get("Year")  # could be int or str
        year_str = str(raw_year or "")  # normalize to string, avoid None

        # If there’s any dash, split on the first occurrence
        for sep in ("–", "-", "—"):
            if sep in year_str:
                year_str = year_str.split(sep)[0]
                break

        try:
            year = int(year_str)
        except (ValueError, TypeError):
            year = None

        raw_genre = data.get("Genre", "")  # e.g. "Action, Adventure, Sci-Fi"
        genre = raw_genre.strip()

        movie = Movie(
            title=data["title"],
            director=data["director"],
            year=year,  # use parsed year
            rating=float(data["rating"]) if data.get("rating") else None,
            poster=data["poster"],
            genre=genre
        )


        db.session.add(movie)
        try:
            db.session.commit()
            flash(f"“{title}” added.", "success")
            return redirect(url_for('main.user_movies', user_id=user_id))
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("DB error adding movie")
            flash("Error saving movie.", "error")
            return render_template('add_movie.html', user_id=user_id)

    return render_template('add_movie.html', user_id=user_id)


@main.route('/users/<int:user_id>/remove_movie/<int:movie_id>', methods=['POST'])
def remove_movie(user_id, movie_id):
    user  = User.query.get_or_404(user_id)
    movie = Movie.query.get_or_404(movie_id)

    if movie not in user.movies:
        # Either 404 or just flash “not in your list”
        abort(404)

    try:
        # Remove the association, not the movie row
        user.movies.remove(movie)
        db.session.commit()
        flash(f"Removed '{movie.title}' from your list.", "success")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("DB error removing movie from user")
        flash("Could not remove movie. Try again.", "error")

    return redirect(url_for('main.user_movies', user_id=user_id))


@main.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET','POST'])
def update_movie(user_id, movie_id):
    movie = Movie.query.get_or_404(movie_id)
    user  = User.query.get_or_404(user_id)

    if request.method == 'POST':
        # 1) Validate inputs
        name = request.form.get('name','').strip()
        if not name:
            flash("Movie title cannot be empty.", "warning")
            return redirect(url_for('main.user_movies', user_id=user_id))

        # 2) Optional fields or fallbacks
        director = request.form.get('director','').strip() or movie.director
        year_str = request.form.get('year','').strip()
        rating_str = request.form.get('rating','').strip()

        # 3) Cast and assign
        try:
            movie.year   = int(year_str)    if year_str   else movie.year
            movie.rating = float(rating_str) if rating_str else movie.rating
            movie.name     = name
            movie.director = director
        except ValueError:
            flash("Year must be an integer and rating a number.", "error")
            return render_template('update_movie.html', user=user, movie=movie)

        # 4) Commit or rollback
        try:
            db.session.commit()
            flash(f"“{movie.name}” has been updated.", "success")
            return redirect(url_for('main.user_movies', user_id=user_id))
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception("DB error updating movie")
            flash("An internal error occurred. Please try again.", "error")
            return render_template('update_movie.html', user=user, movie=movie)

    # GET → show form
    return render_template('update_movie.html', user=user, movie=movie)


@main.route('/users/<int:user_id>/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(user_id, movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if movie.user_id != user_id:
        abort(404)
    try:
        db.session.delete(movie)
        db.session.commit()
        flash(f"Deleted “{movie.name}”", "success")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("DB error deleting movie")
        flash("Could not delete.", "error")
    return redirect(url_for('main.user_movies', user_id=user_id))


@main.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return render_template('search_results.html',
                               query=q, users=[], movies=[])

    try:
        users = User.query.filter(User.name.ilike(f"%{q}%")).all()
        movies = Movie.query.filter(
            or_(
                Movie.title.ilike(f"%{q}%"),
                Movie.director.ilike(f"%{q}%")
            )
        ).all()
    except SQLAlchemyError:
        current_app.logger.exception("DB error during search")
        users, movies = [], []

    return render_template(
        'search_results.html',
        query=q,
        users=users,
        movies=movies
    )