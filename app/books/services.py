import os
import secrets
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime, timedelta, timezone
from ..extensions import db
from ..models import Book

def save_cover_image(form_picture):
    if not form_picture:
        return 'default_book.jpg'
        
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    # Store image data in Redis with a 24-hour expiration (86400 seconds)
    import redis
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/1')
    
    image_data = form_picture.read()
    
    try:
        redis_client = redis.from_url(redis_url)
        redis_key = f"cover_image:{picture_fn}"
        redis_client.setex(redis_key, 86400, image_data)
        
        # Dispatch Celery task to persist image to disk
        from tasks.image_tasks import persist_cover_image
        persist_cover_image.delay(picture_fn)
    except Exception as e:
        print(f"WARNING: Redis/Celery not available ({e}). Falling back to synchronous disk save.")
        upload_path = os.path.join(current_app.root_path, 'static', 'covers')
        os.makedirs(upload_path, exist_ok=True)
        picture_path = os.path.join(upload_path, picture_fn)
        
        with open(picture_path, 'wb') as f:
            f.write(image_data)
            
    # Reset file pointer just in case it's used again
    form_picture.seek(0)
    
    return picture_fn

def create_book(user_id, form_data, cover_image_file):
    cover_filename = save_cover_image(cover_image_file)
    from ..models import User
    
    user = db.session.get(User, user_id)
    
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
        expires_at=datetime.now(timezone.utc) + timedelta(days=5)
    )
    
    db.session.add(book)
    db.session.commit()
    return book

def get_available_books(exclude_user_id=None, page=1, per_page=6):
    five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
    query = Book.query.filter(Book.is_available == True, Book.created_at >= five_days_ago)
    if exclude_user_id:
        query = query.filter(Book.owner_id != exclude_user_id)
    return query.order_by(Book.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

def get_book_by_id(book_id):
    return db.session.get(Book, book_id)
