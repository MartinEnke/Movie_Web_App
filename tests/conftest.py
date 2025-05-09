import pytest
from pathlib import Path
from Movie_Web_App import create_app, db

@pytest.fixture
def app(tmp_path):
    test_db = tmp_path / "test.db"
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{test_db}",
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-secret",
    }
    app = create_app(test_config)

    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
