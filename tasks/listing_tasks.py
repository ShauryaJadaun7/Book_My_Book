from .celery_app import celery
from app.extensions import db
from app.models import Book
from wsgi import app
from datetime import datetime, timezone

@celery.task
def expire_old_listings():
    """
    Checks all currently active books and checks their expires_at date.
    If the current datetime is greater than expires_at, marks is_available = False.
    """
    with app.app_context():
        now = datetime.now(timezone.utc)
        # Find books that are available but past their expiration date.
        expired_books = Book.query.filter(
            Book.is_available == True,
            Book.expires_at != None,
            Book.expires_at <= now
        ).all()

        count = 0
        for book in expired_books:
            book.is_available = False
            count += 1
            
        if count > 0:
            db.session.commit()
            print(f"[Automated Action] Expired {count} books.")
            
    return f"Processed {count} expirations."
