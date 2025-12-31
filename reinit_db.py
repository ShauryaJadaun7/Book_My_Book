from website import create_app, db
# IMPORTANT: Import all models here so SQLAlchemy knows they exist
from website.models import User, Book, BarterRequest, BarterDetail 

app = create_app()

with app.app_context():
    try:
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
        print("Success: Database recreated with all new columns!")
    except Exception as e:
        print(f"An error occurred: {e}")