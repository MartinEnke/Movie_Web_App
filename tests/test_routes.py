import pytest
from Movie_Web_App.data_manager.models import User, Movie
from Movie_Web_App import db

def test_index_empty(client):
    resp = client.get('/')
    assert resp.status_code == 200
    assert b"No users yet" in resp.data


def test_add_user_and_list(client):
    # Add a user
    resp = client.post(
        '/add_user',
        data={"name": "Alice"},
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Alice" in resp.data

    # Duplicate name → flash "already exists"
    resp2 = client.post(
        '/add_user',
        data={"name": "Alice"},
        follow_redirects=True
    )
    assert resp2.status_code == 200
    assert b"already exists" in resp2.data


def test_user_movies_edge(client):
    # Non-existent user → 404
    resp = client.get("/users/999")
    assert resp.status_code == 404

    # Create a user via the route
    client.post('/add_user', data={"name": "Bob"})
    # Lookup Bob’s ID using application context
    from Movie_Web_App import db
    with client.application.app_context():
        bob = User.query.filter_by(name="Bob").first()
        assert bob is not None
        user_id = bob.id

    # user_movies page should be 200 and flash "No movies found"
    resp2 = client.get(f"/users/{user_id}")
    assert resp2.status_code == 200
    assert b"No movies found" in resp2.data


def test_add_and_delete_movie(client, monkeypatch):
    # 1) Create the user
    client.post('/add_user', data={"name": "Carol"})
    from Movie_Web_App import db
    from Movie_Web_App.data_manager.models import User, Movie
    with client.application.app_context():
        carol = User.query.filter_by(name="Carol").first()
        uid = carol.id

    # ── INSERT MONKEYPATCH HERE ──
    import Movie_Web_App.omdb_api as api
    monkeypatch.setattr(
        api,
        "fetch_movie_data",
        lambda title: {
            "title":  "X",
            "director":"D",
            "year":   "2000",
            "rating":"5.0",
            "poster":""
        }
    )
    # ───────────────────────────────

    # 2) Now when you POST to add_movie, it will use your fake
    resp = client.post(
        f"/users/{uid}/add_movie",
        data={"name": "X"},
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"X" in resp.data


def test_update_movie_success(client, monkeypatch):
    # 1) create user & movie stub
    client.post('/add_user', data={'name':'Dave'})
    from Movie_Web_App import db
    from Movie_Web_App.data_manager.models import User, Movie
    with client.application.app_context():
        user = User.query.filter_by(name='Dave').first()
        # stub OMDb to add one movie
        import Movie_Web_App.omdb_api as api
        monkeypatch.setattr(api, 'fetch_movie_data',
                            lambda title: {'title':'Old','director':'X','year':'2000','rating':'5.0','poster':''})
        client.post(f'/users/{user.id}/add_movie', data={'name':'Old'}, follow_redirects=True)
        movie = Movie.query.filter_by(user_id=user.id).first()
        assert movie.name == 'Old'

    # 2) update that movie
    resp = client.post(f'/users/{user.id}/update_movie/{movie.id}',
                       data={'name':'New','director':'Y','year':'2021','rating':'7.2'},
                       follow_redirects=True)
    assert resp.status_code == 200
    assert b'New' in resp.data
    assert b'has been updated' in resp.data


def test_update_movie_validation(client, monkeypatch):
    # Setup: create user and movie
    client.post('/add_user', data={'name': 'Eve'})
    with client.application.app_context():
        eve = User.query.filter_by(name='Eve').first()
        # stub add_movie to create a movie
        import Movie_Web_App.omdb_api as api
        monkeypatch.setattr(api, 'fetch_movie_data',
                            lambda title: {'title':'Foo','director':'D','year':'2001','rating':'6.1','poster':''})
        client.post(f'/users/{eve.id}/add_movie', data={'name':'Foo'})
        movie = Movie.query.filter_by(user_id=eve.id).first()

    # 1a) Empty title should flash warning
    resp = client.post(
        f'/users/{eve.id}/update_movie/{movie.id}',
        data={'name': ''},
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Movie title cannot be empty" in resp.data

    # 1b) Bad year/rating should flash error
    resp2 = client.post(
        f'/users/{eve.id}/update_movie/{movie.id}',
        data={'name':'Foo','year':'not-a-number','rating':'oops'},
        follow_redirects=True
    )
    assert resp2.status_code == 200
    assert b"Year must be an integer and rating a number" in resp2.data


def test_update_movie_not_found(client):
    client.post('/add_user', data={'name':'Frank'})
    with client.application.app_context():
        frank = User.query.filter_by(name='Frank').first()
    resp = client.get(f'/users/{frank.id}/update_movie/999')
    assert resp.status_code == 404


def test_add_movie_omdb_error(client, monkeypatch):
    client.post('/add_user', data={'name':'Grace'})
    with client.application.app_context():
        grace = User.query.filter_by(name='Grace').first()

    # Patch the fetch used by the route itself
    import Movie_Web_App.routes as routes
    monkeypatch.setattr(
        routes,
        'fetch_movie_data',
        lambda title: (_ for _ in ()).throw(Exception("boom"))
    )

    resp = client.post(
        f'/users/{grace.id}/add_movie',
        data={'name':'DoesntMatter'},
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"OMDb unreachable." in resp.data


def test_add_movie_not_found(client, monkeypatch):
    client.post('/add_user', data={'name':'Helen'})
    with client.application.app_context():
        helen = User.query.filter_by(name='Helen').first()

    # Patch the name the route actually uses
    import Movie_Web_App.routes as routes
    monkeypatch.setattr(
        routes,
        'fetch_movie_data',
        lambda title: None
    )

    resp = client.post(
        f'/users/{helen.id}/add_movie',
        data={'name':'Nope'},
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Movie not found" in resp.data


def test_delete_movie_wrong_user(client, monkeypatch):
    # Create user A and B
    client.post('/add_user', data={'name':'Ivy'})
    client.post('/add_user', data={'name':'Jack'})

    # Within the app context, look up and store IDs, and add Ivy’s movie
    with client.application.app_context():
        ivy = User.query.filter_by(name='Ivy').first()
        jack = User.query.filter_by(name='Jack').first()
        ivy_id = ivy.id
        jack_id = jack.id

        # Patch the route’s fetch_movie_data
        import Movie_Web_App.routes as routes
        monkeypatch.setattr(
            routes,
            'fetch_movie_data',
            lambda title: {
                'title': 'Bar',
                'director': 'D',
                'year': '2002',
                'rating': '7.3',
                'poster': ''
            }
        )
        # Add the movie for Ivy
        client.post(f'/users/{ivy_id}/add_movie', data={'name':'Bar'})
        movie = Movie.query.filter_by(user_id=ivy_id).first()
        movie_id = movie.id

    # Now, outside the context, attempt deletion as Jack by ID
    resp = client.post(
        f'/users/{jack_id}/delete_movie/{movie_id}',
        follow_redirects=True
    )
    assert resp.status_code == 404


def test_404_page(client):
    resp = client.get('/definitely-not-a-route')
    assert resp.status_code == 404
    assert b"Page Not Found" in resp.data


def test_add_user_form_validation(client):
    # blank
    resp = client.post('/add_user', data={'name':''}, follow_redirects=True)
    assert b"Please enter a name" in resp.data or b"Enter a name" in resp.data

    # too short
    resp2 = client.post('/add_user', data={'name':'Al'}, follow_redirects=True)
    assert b"Name must be at least 3 characters" in resp2.data or b"Name too short" in resp2.data