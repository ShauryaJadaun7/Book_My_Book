from ..extensions import db
from ..models import CartItem, Book

def add_to_cart(user_id, book_id):
    book = db.session.get(Book, book_id)
    if not book or not book.is_available or not book.is_for_sale:
        return False, "Book is not available for sale."
        
    existing_item = CartItem.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_item:
        return False, "Book is already in your cart."
        
    cart_item = CartItem(user_id=user_id, book_id=book_id)
    db.session.add(cart_item)
    db.session.commit()
    return True, "Added to cart."

def remove_from_cart(user_id, book_id):
    CartItem.query.filter_by(user_id=user_id, book_id=book_id).delete()
    db.session.commit()

def get_cart_items(user_id):
    return CartItem.query.filter_by(user_id=user_id).all()

def clear_cart(user_id):
    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()
