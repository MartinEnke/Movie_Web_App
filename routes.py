from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, abort, current_app
)
from . import db
from .data_manager.models import User, Movie
from .omdb_api import fetch_movie_data
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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
        users = User.query.all() or []
    except SQLAlchemyError:
        current_app.logger.exception("DB error on index")
        abort(500)

    if not users:
        flash("No users yet—why not add one?", "info")
    return render_template('index.html', users=users)

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

@main.route('/users/<int:user_id>')
def user_movies(user_id):
    user = User.query.get_or_404(user_id)
    try:
        movies = current_app.data_manager.get_user_movies(user_id)
    except SQLAlchemyError:
        current_app.logger.exception("DB error fetching movies")
        abort(500)

    if not movies:
        flash("No movies found", "info")
    return render_template('user_movies.html', user=user, movies=movies)

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

        m = Movie(
            name=title,
            director=(data['director'] if data['director']!="N/A" else request.form.get('director','')),
            year=int(data['year']),
            rating=float(data['rating']),
            poster=data['poster'],
            user_id=user_id
        )
        db.session.add(m)
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
