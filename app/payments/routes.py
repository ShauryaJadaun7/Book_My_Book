from flask import render_template, redirect, url_for, flash, request, current_app, Response
from flask_login import login_required, current_user
from . import payments
from .services import process_checkout
from ..cart.services import get_cart_items
from ..models import Transaction, Book
from ..extensions import db
from .upi_service import generate_upi_qr, buyer_confirm, seller_confirm

@payments.route('/checkout', methods=['POST'])
@login_required
def checkout():
    items = get_cart_items(current_user.id)
    if not items:
        flash("Your cart is empty.", "warning")
        return redirect(url_for('cart.view_cart'))
        
    total = sum(item.book.price for item in items if item.book.price)
    try:
        order = process_checkout(current_user.id, items, total)
        transactions = order.get('transactions', [])
        return render_template('payments/checkout.html', 
                               amount=order['amount'], 
                               user=current_user,
                               transactions=transactions)
    except Exception as e:
        flash("Payment processing error. Try again later.", "danger")
        return redirect(url_for('cart.view_cart'))

# --- UPI Payment Routes ---

@payments.route('/upi-qr/<int:tx_id>')
def upi_qr(tx_id):
    tx = db.session.get(Transaction, tx_id)
    if not tx:
        return "Transaction not found", 404
        
    book = db.session.get(Book, tx.book_id)
    upi_id = book.upi_id or book.owner.upi_id
    if not upi_id:
        return "Seller has no UPI ID configured", 400
        
    note = f"BookMyBook: {book.title[:20]}"
    try:
        img_bytes = generate_upi_qr(upi_id, tx.amount, note)
        return Response(img_bytes, mimetype="image/png")
    except Exception as e:
        return f"QR generation failed: {e}", 500

@payments.route('/upi/<int:tx_id>')
@login_required
def upi_checkout(tx_id):
    tx = db.session.get(Transaction, tx_id)
    if not tx or tx.buyer_id != current_user.id or tx.status != 'PENDING':
        flash("Invalid transaction or already processed.", "danger")
        return redirect(url_for('transactions.history'))
    book = db.session.get(Book, tx.book_id)
    if not (book.upi_id or book.owner.upi_id):
        flash("Seller does not support UPI payments.", "danger")
        return redirect(url_for('cart.view_cart'))
    return render_template('payments/upi_checkout.html', tx=tx, book=book)

@payments.route('/upi/confirm/<int:tx_id>', methods=['POST'])
@login_required
def upi_confirm(tx_id):
    upi_ref = request.form.get('upi_ref', '').strip()
    success, msg = buyer_confirm(tx_id, current_user.id, upi_ref)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('transactions.history'))

@payments.route('/upi/pending')
@login_required
def upi_pending():
    # Seller views all transactions awaiting their confirmation
    pending_txs = Transaction.query.filter_by(
        seller_id=current_user.id, 
        status='AWAITING_SELLER_CONFIRMATION'
    ).order_by(Transaction.buyer_confirmed_at.desc()).all()
    return render_template('payments/seller_pending.html', transactions=pending_txs)

@payments.route('/upi/seller-confirm/<int:tx_id>', methods=['POST'])
@login_required
def upi_seller_confirm(tx_id):
    success, msg = seller_confirm(tx_id, current_user.id)
    flash(msg, "success" if success else "danger")
    return redirect(url_for('payments.upi_pending'))
