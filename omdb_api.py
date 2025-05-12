"""
omdb_api.py

Module for interacting with the OMDb API to fetch movie metadata.
"""

import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("OMDB_API_KEY")
URL = "http://www.omdbapi.com/"

def fetch_movie_data(title: str) -> dict | None:
    """
    Query the OMDb API for a given movie title.

    Args:
        title (str): The movie title to search.

    Returns:
        dict: A dictionary containing:
            - title (str)
            - year (int | None)
            - rating (float | None)
            - poster (str)
            - director (str)
            - genre (str)
            - plot (str)
        or None if the movie wasn't found or on error.
    """
    params = {"apikey": API_KEY, "t": title}
    response = requests.get(URL, params=params)
    print("Fetching from OMDb:", response.url)

    if response.status_code != 200:
        print(f"Error fetching data: HTTP {response.status_code}")
        return None

    data = response.json()
    if data.get("Response") != "True":
        print("OMDb says not found:", data.get("Error"))
        return None

    # Parse year (handles ranges like "1967–1987")
    raw_year = data.get("Year", "")
    year_str = str(raw_year)
    for sep in ("–", "-", "—"):
        if sep in year_str:
            year_str = year_str.split(sep, 1)[0]
            break
    try:
        year = int(year_str)
    except (ValueError, TypeError):
        year = None

    # Parse IMDb rating
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
        "genre":    data.get("Genre", "").strip(),
        "plot":     data.get("Plot", "No description available.").strip(),
    }


if __name__ == "__main__":
    # Simple sanity check / demo
    sample = fetch_movie_data("Snatch")
    print("Parsed output:", sample)
