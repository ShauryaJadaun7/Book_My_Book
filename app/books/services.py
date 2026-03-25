import os
import secrets
from werkzeug.utils import secure_filename
from flask import current_app
from ..extensions import db
from ..models import Book

def save_cover_image(form_picture):
    if not form_picture:
        return 'default_book.jpg'
        
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    upload_path = os.path.join(current_app.root_path, 'static', 'covers')
    os.makedirs(upload_path, exist_ok=True)
    picture_path = os.path.join(upload_path, picture_fn)
    
    form_picture.save(picture_path)
    return picture_fn

def create_book(user_id, form_data, cover_image_file):
    cover_filename = save_cover_image(cover_image_file)
    from ..models import User
    
    user = db.session.get(User, user_id)
    upi_id_to_use = form_data.upi_id.data if hasattr(form_data, 'upi_id') and form_data.upi_id.data else (user.upi_id if user else None)
    
    book = Book(
        title=form_data.title.data,
        author=form_data.author.data,
        description=form_data.description.data,
        cover_image=cover_filename,
        owner_id=user_id,
        is_for_sale=form_data.is_for_sale.data,
        price=form_data.price.data if form_data.is_for_sale.data else None,
        is_for_borrow=form_data.is_for_borrow.data,
        borrow_fee_per_day=form_data.borrow_fee_per_day.data if form_data.is_for_borrow.data else None,
        is_for_barter=form_data.is_for_barter.data,
        barter_preferences=form_data.barter_preferences.data if form_data.is_for_barter.data else None,
        upi_id=upi_id_to_use
    )
    
    db.session.add(book)
    db.session.commit()
    return book

def get_available_books(exclude_user_id=None):
    query = Book.query.filter_by(is_available=True)
    if exclude_user_id:
        query = query.filter(Book.owner_id != exclude_user_id)
    return query.order_by(Book.created_at.desc()).all()

def get_book_by_id(book_id):
    return db.session.get(Book, book_id)
