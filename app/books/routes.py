from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import books
from .forms import UploadBookForm
from .services import create_book, get_available_books, get_book_by_id
from ..models import Book

@books.route('/')
def index():
    exclude_id = current_user.id if current_user.is_authenticated else None
    all_books = get_available_books(exclude_user_id=exclude_id)
    return render_template('books/index.html', books=all_books)

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
