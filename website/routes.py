from flask import Blueprint, request, abort
from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from .models import Book, BookOption, BorrowRequest, BarterRequest, BarterDetail
from . import db

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    if current_user.is_authenticated:
        #give all books on  main page
        books = (
    db.session.query(Book, BookOption)
    .join(BookOption, Book.id == BookOption.book_id)
    .filter(BookOption.is_active == True)
    .all()
)

        return render_template('home.html', books=books)            
        return redirect(url_for('routes.home'))
    
    
    return redirect(url_for('auth.register'))

@routes.route('/upload', methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        genre = request.form.get('genre')
        image = request.form.get('image')
        optional_description = request.form.get('optional_description')
        option_type = request.form.get('option_type')  # sell | borrow | barter

        # Create book
        new_book = Book(
            title=title,
            author=author,
            genre=genre,
            image=image,
            description=optional_description,
            owner_id=current_user.id
        )

        db.session.add(new_book)
        db.session.commit()   # Commit book to get its ID for foreign key in BookOption

        # Create book option
        new_book_option = BookOption(
            book_id=new_book.id,
            option_type=option_type
        )

        db.session.add(new_book_option)
        db.session.commit()

        return redirect(url_for('routes.mybooks'))

    return render_template('upload.html')


@routes.route('/mybooks')
@login_required
def mybooks():
    # My listed books
    my_books = Book.query.filter_by(owner_id=current_user.id).all()

    # Incoming borrow requests on my books
    borrow_requests = (
        BorrowRequest.query
        .join(Book)
        .filter(Book.owner_id == current_user.id)
        .all()
    )

    # Incoming barter requests on my books
    barter_requests = (
        BarterRequest.query
        .join(Book, BarterRequest.requested_book_id == Book.id)
        .filter(Book.owner_id == current_user.id)
        .all()
    )

    return render_template(
        'mybooks.html',
        my_books=my_books,
        borrow_requests=borrow_requests,
        barter_requests=barter_requests
    )


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
    offered_book_title = request.form.get('offered_book_title')
    offered_book_genre = request.form.get('offered_book_genre')
    offered_book_image = request.form.get('offered_book_image')
    message = request.form.get('message')

    barter = BarterRequest(
        requested_book_id=book_id,
        requester_id=current_user.id,
        offered_book_title=offered_book_title,
        offered_book_genre=offered_book_genre,
        offered_book_image=offered_book_image,
        message=message
    )

    db.session.add(barter)
    db.session.commit()

    flash('Barter request sent successfully', 'success')
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
