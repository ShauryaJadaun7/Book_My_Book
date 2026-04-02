from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import books
from .forms import UploadBookForm
from .services import create_book, get_available_books, get_book_by_id
from ..models import Book

@books.route('/')
def index():
    exclude_id = current_user.id if current_user.is_authenticated else None
    all_books = get_available_books(exclude_id)
    return render_template('books/index.html', books=all_books)

@books.route('/search')
def search():
    exclude_id = current_user.id if current_user.is_authenticated else None
    q = request.args.get('q', '').strip()
    
    from ..extensions import db
    from datetime import datetime, timedelta, timezone
    
    five_days_ago = datetime.now(timezone.utc) - timedelta(days=5)
    query = Book.query.filter(Book.is_available == True, Book.created_at >= five_days_ago)
    if exclude_id:
        query = query.filter(Book.owner_id != exclude_id)
        
    if q:
        query = query.filter(db.or_(Book.title.ilike(f'%{q}%'), Book.author.ilike(f'%{q}%')))
        
    books = query.order_by(Book.created_at.desc()).all()
    return render_template('books/partials/book_grid.html', books=books)

@books.route('/covers/<filename>')
def serve_cover(filename):
    import redis
    import os
    from flask import current_app, send_from_directory, Response
    
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/1')
    try:
        redis_client = redis.from_url(redis_url)
        redis_key = f"cover_image:{filename}"
        image_data = redis_client.get(redis_key)
        
        if image_data:
            mimetype = 'image/jpeg'
            if filename.lower().endswith('.png'):
                mimetype = 'image/png'
            elif filename.lower().endswith('.gif'):
                mimetype = 'image/gif'
            elif filename.lower().endswith('.webp'):
                mimetype = 'image/webp'
                
            return Response(image_data, mimetype=mimetype)
    except Exception as e:
        print(f"Redis serve_cover error: {e}")
        
    # Fallback to filesystem
    upload_path = os.path.join(current_app.root_path, 'static', 'covers')
    return send_from_directory(upload_path, filename)


@books.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadBookForm()
    if form.validate_on_submit():
        # form.cover_image.data gives the uploaded file in Flask-WTF
        book = create_book(current_user.id, form, form.cover_image.data)
        flash('Book uploaded successfully!', 'success')
        return redirect(url_for('books.detail', book_id=book.id))
    return render_template('books/upload.html', form=form)

@books.route('/<int:book_id>')
def detail(book_id):
    book = get_book_by_id(book_id)
    if not book:
        flash('Book not found.', 'danger')
        return redirect(url_for('books.index'))
    return render_template('books/detail.html', book=book)

@books.route('/my-books')
@login_required
def my_books():
    user_books = Book.query.filter_by(owner_id=current_user.id).order_by(Book.id.desc()).all()
    return render_template('books/my_books.html', books=user_books)
