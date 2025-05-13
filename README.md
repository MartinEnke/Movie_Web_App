# 🎬 CineFlick – Your Personal Movie Catalog
A sleek, responsive Flask web app that lets you browse, curate and review movies.  
Under the hood it uses OMDb for metadata, SQLAlchemy & Alembic for persistence & migrations, and Tailwind CSS + Alpine.js for a modern UI.

index
  ![Banner](static/banner1.png)
user_movies
  ![Banner](static/banner2.png)
movie_details (+ review section below)
  ![Banner](static/banner3.png) 




---

## 🚀 Features

- **Global Catalog**  
  Browse a seeded library of films (posters, titles, years, genres, plots).

- **Personal Lists**  
  Create users and maintain individual “favorite movies” lists via many-to-many association.

- **Search & Filter**  
  • Free-text search on titles & directors  
  • Genre-based filtering  
  • Per-user catalog search with “Add / In List” indicators

- **Reviews**  
  Anonymous user reviews & star ratings, stored per movie.

- **Mobile-First Design**  
  Responsive grid of movie cards, translucent “milky” overlays, persistent top navbar with hamburger menu.

---

## 🛠 Tech Stack & Tools

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.13-blue">  
  <img alt="Flask"   src="https://img.shields.io/badge/Flask-2.3-lightgrey">  
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.0-yellow">  
  <img alt="Alembic" src="https://img.shields.io/badge/Alembic-1.15-orange">  
  <img alt="SQLite"  src="https://img.shields.io/badge/SQLite-3.43-lightblue">  
  <img alt="Tailwind" src="https://img.shields.io/badge/TailwindCSS-3.4-teal">  
  <img alt="Alpine.js" src="https://img.shields.io/badge/Alpine.js-3.x-green">  
  <img alt="OMDb API" src="https://img.shields.io/badge/OMDb_API-free-red">  
</p>

- **Flask** – lightweight web framework  
- **Flask-Migrate/Alembic** – DB migrations  
- **Flask-SQLAlchemy** – ORM  
- **SQLite** – file-based relational DB  
- **Tailwind CSS** – utility-first styling via CDN  
- **Alpine.js** – minimal JS interactivity (dropdowns, mobile nav)  
- **requests + python-dotenv** – OMDb API integration  
- **pytest** – unit & functional tests  

---

## 🏗️ Getting Started

1. **Clone & 🔧 Configure**  
   ```bash
   git clone https://github.com/yourusername/CineSis.git
   cd CineSis
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env   # add your OMDb key


2. **Database & Migrations**

    ```bash
    flask db init
    flask db migrate -m "Initial schema"
    flask db upgrade

2. **Seeding the Catalog**
Provide a newline-separated seed_titles.txt of movie names, then:

    ```bash
    flask seed-movies seed_titles.txt

4. **Run the App**

    ```bash
    flask run --port 5030
    # or
    python manage.py
   
Visit http://127.0.0.1:5030 in your browser.


🧪 **Testing**

    pytest

Tests cover routing, edge cases (OMDb errors, duplicates), and DB operations.**


📂 **Project Structure**

    pgsql
```
.
├── CineSis/                # Flask app package
│   ├── __init__.py         # create_app & extensions
│   ├── routes.py           # all @main blueprint views
│   ├── omdb_api.py         # OMDb wrapper + safe parsing
│   ├── data_manager/       # SQLAlchemy models & manager
│   ├── templates/          # Jinja2 HTML + Tailwind components
│   └── static/
│       ├── custom.css
│       └── assets/         # images, icons, banner placeholder
├── manage.py               # CLI entrypoint + Flask-Migrate setup
├── seed_titles.txt         # sample list of movies to seed
├── requirements.txt
├── pytest.ini
└── README.md
```

## Future Ideas for CineFlick

1. **User Accounts & Authentication**  
   - Sign up / Log in (e.g. Flask-Login) so users manage their own lists.  
   - OAuth integration (Google, GitHub) for one-click access.

2. **Packaging & Deployment**  
   - Dockerized development and production images.  
   - CI/CD pipeline (GitHub Actions) with automated tests, linting, and deploy.  
   - Hosting options: Heroku, AWS, GCP, or self-hosted.
   
3. **Integrating AI Features**
   - Movie Recommendation: based on the users favorite movies (also possible without AI).
   - Movie Trivia: trivia question and answer game about movies to entertain users.

4. **Recommendations & Discovery**  
   - “Similar movies” suggestions based on genre overlap or collaborative filtering.  
   - “People also watched…” section from aggregated user data.  
   - Trending / New releases feed pulled from an external API.

5. **Advanced Search & Filters**  
   - Multi-criteria search (combine director, year range, rating threshold).  
   - User-defined tags (e.g. “campy,” “arthouse,” “holiday watch”).  
   - Saved searches or “smart playlists” that auto-update.
   
6. **Social & Sharing**  
   - Follow other users & browse their public lists.  
   - Shareable list URLs or “public profile” pages.  
   - Avatars/Gravatars and social-login comments on reviews.

7. **Rich Media & Integrations**  
   - Embed trailers via the YouTube API on detail pages.  
   - Full-screen poster galleries with lightbox views.  
   - Mobile push notifications for new releases or friend activity.

8. **Rich Reviews & Ratings**  
   - Star-rating widget (½-stars, dynamic bars) instead of raw numeric input.  
   - Review moderation (flag inappropriate content).  
   - Threaded replies under reviews for community discussion.

9. **Internationalization & Accessibility**  
   - Multi-language support with Flask-Babel.  
   - ARIA tags, high-contrast mode, and screen-reader–friendly layouts.

10. **Analytics & Dashboards**  
   - Personal stats page: total films tracked, average rating, top genres.  
   - Community leaderboards (most active users, highest-rated films).


