from flask import render_template
from flask_login import login_required, current_user
from . import transactions
from ..models import Transaction

@transactions.route('/history')
@login_required
def history():
    purchases = Transaction.query.filter(
        Transaction.buyer_id == current_user.id,
        Transaction.status.in_(['COMPLETED', 'AWAITING_SELLER_CONFIRMATION', 'PENDING'])
    ).order_by(Transaction.created_at.desc()).all()
    
    sales = Transaction.query.filter(
        Transaction.seller_id == current_user.id,
        Transaction.status == 'COMPLETED'
    ).order_by(Transaction.created_at.desc()).all()
    
    return render_template('transactions/history.html', purchases=purchases, sales=sales)
