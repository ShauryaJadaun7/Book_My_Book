from datetime import datetime, timedelta, timezone
from ..extensions import db
from ..models import BorrowRecord, Book, Notification, User


def request_borrow(book_id, borrower_id, days):
    book = db.session.get(Book, book_id)
    if not book or not book.is_for_borrow:
        return False, "Book unavailable for borrowing."
    if not book.is_available:
        return False, "This book is currently unavailable."

    borrower = db.session.get(User, borrower_id)

    record = BorrowRecord(
        book_id=book_id,
        borrower_id=borrower_id,
        owner_id=book.owner_id,
        requested_days=days
    )
    db.session.add(record)
    db.session.flush()  # get record.id before commit

    fee_info = (
        f"₹{book.borrow_fee_per_day}/day borrow fee"
        if book.borrow_fee_per_day
        else "no borrow fee set"
    )

    notif = Notification(
        user_id=book.owner_id,
        title="New Borrow Request",
        message=(
            f"{borrower.full_name or 'Someone'} wants to borrow '{book.title}' "
            f"for {days} day(s).\n\n"
            f"📧 Email: {borrower.email}\n"
            f"📞 Phone: {borrower.phone or 'not provided'}\n\n"
            f"💰 Payment note: {fee_info}. "
            f"If you accept, please collect payment directly from them."
        ),
        ref_type='BORROW',
        ref_id=record.id,
        actionable=True
    )
    db.session.add(notif)
    db.session.commit()
    return True, "Borrow request sent."


def respond_borrow(record_id, owner_id, action):
    record = db.session.get(BorrowRecord, record_id)
    if not record or record.owner_id != owner_id:
        return False, "Invalid borrow record."

    # Mark the actionable notification as done
    notif = Notification.query.filter_by(ref_type='BORROW', ref_id=record_id, actionable=True).first()

    if action == 'APPROVE':
        record.status = 'ACTIVE'
        record.start_date = datetime.now(timezone.utc)
        record.due_date = record.start_date + timedelta(days=record.requested_days)

        book = db.session.get(Book, record.book_id)
        if book:
            book.is_available = False

        owner = db.session.get(User, owner_id)
        fee_info = (
            f"₹{book.borrow_fee_per_day}/day"
            if book and book.borrow_fee_per_day
            else "the agreed amount"
        )

        # Notify borrower — include owner contact + payment reminder
        db.session.add(Notification(
            user_id=record.borrower_id,
            title="Borrow Request Approved ✅",
            message=(
                f"Your request to borrow '{book.title}' was approved!\n\n"
                f"📧 Owner email: {owner.email}\n"
                f"📞 Owner phone: {owner.phone or 'not provided'}\n\n"
                f"💰 Please pay {fee_info} directly to the owner before collecting. "
                f"Due date: {record.due_date.strftime('%d %b %Y')}."
            )
        ))

        if notif:
            notif.is_read = True
            notif.actionable = False

        db.session.commit()
        return True, "Request approved."

    elif action == 'REJECT':
        record.status = 'REJECTED'
        book = db.session.get(Book, record.book_id)

        db.session.add(Notification(
            user_id=record.borrower_id,
            title="Borrow Request Rejected ❌",
            message=(
                f"Your request to borrow '{book.title if book else 'the book'}' "
                f"was not accepted by the owner."
            )
        ))

        if notif:
            notif.is_read = True
            notif.actionable = False

        db.session.commit()
        return True, "Request rejected."

    return False, "Invalid action."


def return_borrow(record_id, borrower_id):
    record = db.session.get(BorrowRecord, record_id)
    if not record or record.borrower_id != borrower_id or record.status != 'ACTIVE':
        return False, None, "Cannot return this book."

    now = datetime.now(timezone.utc)
    
    # Calculate exactly how many days the user kept the book
    if record.start_date:
        start_date = record.start_date.replace(tzinfo=timezone.utc) if record.start_date.tzinfo is None else record.start_date
        days_kept = (now - start_date).days
        if days_kept < 1:
            days_kept = 1
    else:
        days_kept = 1

    late_fee = 0.0
    if record.due_date:
        due_date = record.due_date.replace(tzinfo=timezone.utc) if record.due_date.tzinfo is None else record.due_date
        if now > due_date:
            days_late = (now - due_date).days + 1
            late_fee = days_late * 5.0  # ₹5 per day late fee

    record.late_fee_accrued = late_fee
    db.session.commit()

    book = db.session.get(Book, record.book_id)
    borrow_fee = (book.borrow_fee_per_day or 0.0) * days_kept
    total_fee = borrow_fee + late_fee
    
    data = {
        "borrow_fee": borrow_fee, 
        "late_fee": late_fee, 
        "total": total_fee, 
        "record": record,
        "days_kept": days_kept
    }

    return True, data, "Proceed to pay."

def confirm_return(record_id, owner_id):
    record = db.session.get(BorrowRecord, record_id)
    if not record or record.owner_id != owner_id:
        return False, "Invalid borrow record."
        
    if record.status != 'RETURN_PENDING_CONFIRMATION':
        return False, "This book is not pending return confirmation."
        
    record.status = 'RETURNED'
    
    book = db.session.get(Book, record.book_id)
    if book:
        book.is_available = True
        
    # Notify borrower that return is complete
    db.session.add(Notification(
        user_id=record.borrower_id,
        title="Return Confirmed ✅",
        message=f"The owner has confirmed receipt and payment for '{book.title if book else 'the book'}'. Thank you!"
    ))
        
    db.session.commit()
    return True, "Return confirmed and book re-listed."
