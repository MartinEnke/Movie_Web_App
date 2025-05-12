import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")
URL = "http://www.omdbapi.com/"

def fetch_movie_data(title):
    """
    Fetches movie data from the OMDb API by title.
    Returns a dict with safe 'year' (int or None), rating, poster, director.
    """
    params = {"apikey": API_KEY, "t": title}
    response = requests.get(URL, params=params)
    print("Fetching from OMDb:", response.url)

    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return None

    data = response.json()
    print("OMDb raw response: Year=", data.get("Year"), "Genre=", data.get("Genre"))
    if data.get("Response") != "True":
        print("OMDb says not found:", data.get("Error"))
        return None

    # Safe‐year parsing (handles ranges like "1967–1987")
    raw_year = data.get("Year", "")
    year_str = str(raw_year)
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

    # Safe rating parsing
    imdb_rating = data.get("imdbRating", "")
    try:
        rating = float(imdb_rating) if imdb_rating not in ("N/A", "") else None
    except ValueError:
        rating = None

    return {
        "title":    data.get("Title", "").strip(),
        "year":     year,
        "rating":   rating,
        "poster":   data.get("Poster", "").strip(),
        "director": data.get("Director", "").strip(),
        "genre": genre,
        "plot": data.get("Plot", "No description available.")
    }

fetch_movie_data("Snatch")