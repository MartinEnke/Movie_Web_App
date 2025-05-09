from Movie_Web_App import create_app, db

app = create_app()

if __name__ == '__main__':
    # with app.app_context():
    #     db.drop_all()  # Drops all tables in the database
    #     db.create_all()  # Creates the tables again based on models
    #     print("Tables created successfully!")
    app.run(debug=True, port=5030)