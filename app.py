"""
app.py

Entry point for running the MovieWeb Flask application.
"""

from Movie_Web_App import create_app, db

# Create the Flask application instance using the factory
app = create_app()

def main():
    """
    Run the Flask development server.
    - Debug mode: on (with reloader and debugger).
    - Port: 5030 by default.
    """
    app.run(debug=True, port=5030)

if __name__ == '__main__':
    main()