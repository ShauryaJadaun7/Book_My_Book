from .celery_app import celery
from app import create_app
from app.extensions import db
from app.models import BorrowRecord, Notification
from datetime import datetime, timezone

@celery.task
def check_overdue_books():
    app = create_app('default')
    with app.app_context():
        now = datetime.now(timezone.utc)
        overdue_records = BorrowRecord.query.filter(
            BorrowRecord.status == 'ACTIVE',
            BorrowRecord.due_date < now
        ).all()
        
        count = 0
        for record in overdue_records:
            # Send notification to borrower
            notif = Notification(
                user_id=record.borrower_id,
                title="Overdue Book!",
                message=f"Your borrowed book is overdue. Please return it as soon as possible to avoid further late fees."
            )
            db.session.add(notif)
            
            # Send notification to owner
            notif_owner = Notification(
                user_id=record.owner_id,
                title="Book Overdue",
                message=f"A book you lent is currently overdue."
            )
            db.session.add(notif_owner)
            count += 2
            
        db.session.commit()
        return f"Checked overdue books. Sent {count} notifications."
