from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import borrows
from .services import request_borrow as services_request_borrow, respond_borrow, return_borrow
from ..models import BorrowRecord, Book

@borrows.route('/request/<int:book_id>', methods=['POST'])
@login_required
def request_borrow(book_id):
    days = int(request.form.get('requested_days', 7))
    success, msg = services_request_borrow(book_id, current_user.id, days)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('books.detail', book_id=book_id))

@borrows.route('/incoming')
@login_required
def incoming():  # render all incoming at one page
    records = BorrowRecord.query.filter_by(owner_id=current_user.id, status='REQUESTED').all()
    active = BorrowRecord.query.filter_by(owner_id=current_user.id).filter(BorrowRecord.status.in_(['ACTIVE', 'RETURN_PENDING_CONFIRMATION'])).all()
    return render_template('borrows/incoming.html', requested=records, active=active)

@borrows.route('/my_borrows')
@login_required
def my_borrows():
    # Shows books the current user has borrowed
    active_borrows = BorrowRecord.query.filter_by(borrower_id=current_user.id).filter(BorrowRecord.status.in_(['ACTIVE', 'RETURN_PENDING_CONFIRMATION'])).all()
    past_borrows = BorrowRecord.query.filter_by(borrower_id=current_user.id, status='RETURNED').all()
    return render_template('borrows/my_borrows.html', active_borrows=active_borrows, past_borrows=past_borrows)

@borrows.route('/respond/<int:record_id>/<action>', methods=['POST'])
@login_required
def respond(record_id, action):
    success, msg = respond_borrow(record_id, current_user.id, action.upper())
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('borrows.incoming'))

@borrows.route('/return_book/<int:record_id>', methods=['GET', 'POST'])
@login_required
def return_book(record_id):
    success, data, msg = return_borrow(record_id, current_user.id)
    if not success:
        flash(msg, 'danger')
        return redirect(url_for('core.index'))
    
    if request.method == 'POST':
        # Simulated payment completion for return.
        # In a real app, integrate Razorpay here like in payments/checkout.
        record = data['record']
        record.status = 'RETURN_PENDING_CONFIRMATION'
        
        from datetime import datetime, timezone
        from ..models import Notification
        from ..extensions import db
        
        record.returned_date = datetime.now(timezone.utc)
        
        book = Book.query.get(record.book_id)
        db.session.add(Notification(
            user_id=record.owner_id,
            title="Book Return Pending Confirmation",
            message=f"{current_user.full_name or 'The borrower'} has returned '{book.title if book else 'the book'}' and completed payment. Please check your incoming requests to confirm receipt.",
            ref_type='BORROW',
            ref_id=record.id,
            actionable=False
        ))
        
        db.session.commit()
        flash("Payment successful! The return is now pending confirmation from the owner.", "success")
        return redirect(url_for('core.index'))
        
    return render_template('borrows/return.html', data=data)

@borrows.route('/confirm_return/<int:record_id>', methods=['POST'])
@login_required
def confirm_return_route(record_id):
    from .services import confirm_return as services_confirm_return
    success, msg = services_confirm_return(record_id, current_user.id)
    
    from ..models import Notification
    notif = Notification.query.filter_by(ref_type='BORROW', ref_id=record_id, actionable=True, user_id=current_user.id).first()
    if notif:
        notif.is_read = True
        notif.actionable = False
        from ..extensions import db
        db.session.commit()
        
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('borrows.incoming'))
