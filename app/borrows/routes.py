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
    active = BorrowRecord.query.filter_by(owner_id=current_user.id, status='ACTIVE').all()
    return render_template('borrows/incoming.html', requested=records, active=active)

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
        record.status = 'RETURNED'
        
        from datetime import datetime, timezone
        record.returned_date = datetime.now(timezone.utc)
        book = Book.query.get(record.book_id)
        if book:
            book.is_available = True
        
        from ..extensions import db
        db.session.commit()
        flash("Book returned and fees paid. Thank you!", "success")
        return redirect(url_for('core.index'))
        
    return render_template('borrows/return.html', data=data)
