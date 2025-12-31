import datetime
from flask import Blueprint, app, request, abort, current_app
from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from .models import Book, BookOption, BorrowDetail, BorrowRequest, BarterRequest, BarterDetail, SellDetail
from . import db

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    if current_user.is_authenticated:
        # Hide my own books if logged in
        all_books = Book.query.filter(Book.owner_id != current_user.id).all()
    else:
        # Show all books to guests
        all_books = Book.query.all()
    
    return render_template('home.html', books=all_books)
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import os

import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@routes.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # 1. Collect basic info
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        description = request.form.get('description')
        listing_type = request.form.get('listing_type') # 'buy', 'borrow', or 'barter'
        
        # 2. Handle Image
        file = request.files.get('image')
        filename = secure_filename(file.filename)
        unique_name = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{filename}"
        file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name))

        # 3. Create the Book first
        new_book = Book(
            title=title, author=author, genre=genre,
            description=description, image=unique_name,
            owner_id=current_user.id
        )
        db.session.add(new_book)
        db.session.flush() # This gives us new_book.id without committing yet

        # 4. Create the specific detail based on listing_type
        if listing_type == 'buy':
            price = request.form.get('price', 0)
            detail = SellDetail(book_id=new_book.id, price=float(price))
            db.session.add(detail)
        elif listing_type == 'borrow':
            detail = BorrowDetail(book_id=new_book.id, per_day_fee=0, late_fee=0)
            db.session.add(detail)
        
        # Create a BookOption entry so the app knows what type this book is
        option = BookOption(book_id=new_book.id, option_type=listing_type)
        db.session.add(option)

        db.session.commit()
        flash('Book uploaded successfully!', 'success')
        return redirect(url_for('routes.home'))

    return render_template('upload.html')

@routes.route('/mybooks')
@login_required
def mybooks():
    # 1. Fetch your listings
    listings = Book.query.filter_by(owner_id=current_user.id).all()

    # 2. Fetch Borrow Requests
    borrow_reqs = BorrowRequest.query.join(Book).filter(Book.owner_id == current_user.id).all()

    # 3. Fetch Barter Requests
    barter_reqs = BarterRequest.query.join(Book, BarterRequest.requested_book_id == Book.id).filter(Book.owner_id == current_user.id).all()

    # 4. Combine them into one list
    combined_requests = []
    for req in borrow_reqs:
        req.type = 'borrow'  # Tag them so the HTML knows which is which
        combined_requests.append(req)
    for req in barter_reqs:
        req.type = 'barter'
        combined_requests.append(req)

    return render_template(
        'mybooks.html',
        listings=listings,
        requests=combined_requests  # Send as one unified list
    )
@routes.route('/buy/<int:book_id>')
@login_required
def buy_book(book_id):
    flash("Payment feature coming soon", "info")
    return redirect(url_for('routes.home'))

@routes.route('/borrow/<int:book_id>', methods=['POST'])
@login_required
def borrow_book(book_id):
    days = request.form.get('days')
    message = request.form.get('message')

    borrow = BorrowRequest(
        book_id=book_id,
        borrower_id=current_user.id,
        days=days,
        message=message
    )
    db.session.add(borrow)
    db.session.commit()

    flash('Borrow request sent', 'success')
    return redirect(url_for('routes.home'))




@routes.route('/barter/<int:book_id>', methods=['POST'])
@login_required
def barter_book(book_id):
    # 1. Handle the Image Upload
    image_filename = None
    if 'offered_book_image' in request.files:
        file = request.files['offered_book_image']
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_name = f"barter_{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name))
            image_filename = unique_name

    # 2. Create the Request with all fields
    new_request = BarterRequest(
        requested_book_id=book_id,
        requester_id=current_user.id,
        offered_book_title=request.form.get('offered_book_title'),
        offered_book_author=request.form.get('offered_book_author'), # Now valid!
        offered_book_genre=request.form.get('offered_book_genre'),
        offered_book_image=image_filename,                           # Now valid!
        message=request.form.get('message'),
        status='pending'
    )
    
    db.session.add(new_request)
    db.session.commit()
    flash('Barter offer sent!', 'success')
    return redirect(url_for('routes.home'))
@routes.route('/request/<string:req_type>/<int:req_id>/<string:action>', methods=['POST'])
@login_required
def handle_request(req_type, req_id, action):

    # Map request type to model
    model_map = {
        'borrow': BorrowRequest,
        'barter': BarterRequest,
    }

    Model = model_map.get(req_type)
    if not Model:
        abort(404)

    request_obj = Model.query.get_or_404(req_id)

    #Security: only book owner can accept/reject
    if request_obj.book.owner_id != current_user.id:
        abort(403)

    if action == 'accept':
        request_obj.status = 'accepted'

        # Optional: auto reject other pending requests for same book
        Model.query.filter(
            Model.book_id == request_obj.book_id,
            Model.id != request_obj.id,
            Model.status == 'pending'
        ).update({'status': 'rejected'})

    elif action == 'reject':
        request_obj.status = 'rejected'

    else:
        abort(400)

    db.session.commit()
    flash(f'Request {action}ed successfully', 'success')
    return redirect(url_for('routes.mybooks'))

# @app.errorhandler(404)
# def page_not_found(e):
#     return render_template('404.html'), 404
