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
    Returns a dict with year, rating, poster if successful, or None if not found.
    """
    params = {"apikey": API_KEY, "t": title}
    response = requests.get(URL, params=params)

    print("Fetching from OMDb:", response.url)  # Log the request URL for debugging
    if response.status_code == 200:
        data = response.json()

        if data.get("Response") == "True":
            print("Movie data fetched successfully:", data)  # Log the fetched data
            return {
                "title": data["Title"],
                "year": int(data["Year"]),
                "rating": float(data["imdbRating"]) if data["imdbRating"] != "N/A" else 0.0,
                "poster": data.get("Poster", ""),
                "director": data.get("Director", "")
            }
        else:
            print("Error: Movie not found in OMDb database.")  # Log error message
            return None
    else:
        print(f"Error fetching data from OMDb API: {response.status_code}")  # Log response code
        return None
