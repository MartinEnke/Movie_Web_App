# manage.py  (located in the project root outside the repo)
from Movie_Web_App.app import create_app, db
from flask_migrate import Migrate
import click
from Movie_Web_App.data_manager.models import Movie
from Movie_Web_App.omdb_api import fetch_movie_data

app = create_app()
migrate = Migrate(app, db)

@app.cli.command("seed-movies")
@click.argument("titles_file", type=click.Path(exists=True))
def seed_movies(titles_file):
    """Seed the movies table from a newline-separated file of titles."""
    with app.app_context():
        count = 0
        for line in open(titles_file, encoding="utf-8"):
            title = line.strip()
            if not title or Movie.query.filter_by(title=title).first():
                click.echo(f"Skipping: {title}")
                continue
            data = fetch_movie_data(title)
            if not data:
                click.echo(f"Not found in OMDb: {title}")
                continue

            movie = Movie(
                title    = data["title"],
                director = data["director"],
                year     = data.get("year"),
                rating   = data.get("rating"),
                poster   = data.get("poster"),
                genre    = data.get("genre", ""),
                plot     = data.get("plot", "")
            )
            db.session.add(movie)
            count += 1
            click.echo(f"Added: {movie.title} ({movie.year})")

        db.session.commit()
        click.echo(f"Done—{count} new movies added.")

@app.cli.command("remove-movie")
@click.argument("movie_id", type=int)
def remove_movie_cli(movie_id):
    """Remove a movie from the catalog by its ID."""
    with app.app_context():
        m = Movie.query.get(movie_id)
        if not m:
            click.echo(f"No movie with ID {movie_id}")
            return
        db.session.delete(m)
        db.session.commit()
        click.echo(f"Deleted movie {m.title} (ID {movie_id})")

if __name__ == "__main__":
    app.run(debug=True, port=5030)
