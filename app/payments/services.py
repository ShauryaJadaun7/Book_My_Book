from flask import current_app
from ..extensions import db
from ..models import Transaction, Book, CartItem

def process_checkout(user_id, cart_items, total_amount):
    # Create PENDING transactions
    transactions = []
    
    for item in cart_items:
        tx = Transaction(
            tx_type='SALE',
            book_id=item.book_id,
            buyer_id=user_id,
            seller_id=item.book.owner_id,
            amount=item.book.price,
            status='PENDING'
        )
        db.session.add(tx)
        transactions.append(tx)
    
    db.session.commit()
    
    # Empty cart after checkout processing
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    
    return {
        'id': f'txn_batch_{user_id}_{len(transactions)}', 
        'amount': int(total_amount * 100),
        'transactions': transactions
    }
