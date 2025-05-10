'''
Seeding movies:
Edit:
cd Movie_Web_App
export FLASK_APP=Movie_Web_App.manage:app
flask db upgrade
flask seed-movies seed_titles.txt



'''
from Movie_Web_App.app import app, db
from Movie_Web_App.data_manager.models import Movie
from Movie_Web_App.omdb_api import fetch_movie_data
import click

@app.cli.command("seed-movies")
@click.argument("titles_file", type=click.Path(exists=True))
def seed_movies(titles_file):
    """Seed the movies table from a newline-separated file of titles."""
    with app.app_context():
        count = 0
        with open(titles_file, encoding="utf-8") as f:
            for line in f:
                title = line.strip()
                if not title:
                    continue

                if Movie.query.filter_by(title=title).first():
                    click.echo(f"Skipping: {title}")
                    continue

                data = fetch_movie_data(title)
                if not data:
                    click.echo(f"Not found in OMDb: {title}")
                    continue

                # **Use lowercase** keys from your wrapper
                # year is already parsed as int or None
                year  = data.get("year")

                # genre likewise
                genre = data.get("genre", "").strip()

                movie = Movie(
                    title    = data["title"],
                    director = data["director"],
                    year     = year,
                    rating   = data["rating"],
                    poster   = data["poster"],
                    genre    = genre
                )
                db.session.add(movie)
                count += 1
                click.echo(f"Added: {movie.title} ({movie.year})")

        db.session.commit()
        click.echo(f"Done—{count} new movies added.")


# Delete individual movies via CLI
# Run this in the Terminal:
# flask remove-movie 42      # 42 = id of movie
@app.cli.command("remove-movie")
@click.argument("movie_id", type=int)
def remove_movie_cli(movie_id):
    """Remove a movie from the catalog by its ID."""
    from Movie_Web_App.data_manager.models import Movie
    with app.app_context():
        m = Movie.query.get(movie_id)
        if not m:
            click.echo(f"No movie with ID {movie_id}")
            return
        title = m.title
        db.session.delete(m)
        db.session.commit()
        click.echo(f"Deleted movie {title} (ID {movie_id})")
