from datetime import datetime, date
from flask_login import UserMixin
from . import db


# ================= USER =================
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= BOOK =================
class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    genre = db.Column(db.String(100))
    image = db.Column(db.String(255))

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('User', backref='books')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ================= BOOK OPTIONS =================
class BookOption(db.Model):
    __tablename__ = 'book_options'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    option_type = db.Column(db.String(20), nullable=False)  
    is_active = db.Column(db.Boolean, default=True)

    book = db.relationship('Book', backref='options')


# ================= SELL =================
class SellDetail(db.Model):
    __tablename__ = 'sell_details'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), unique=True)
    price = db.Column(db.Float, nullable=False)

    book = db.relationship('Book', backref='sell_detail')


# ================= BORROW =================
class BorrowDetail(db.Model):
    """
    Owner sets borrow rules here
    """
    __tablename__ = 'borrow_details'

    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), unique=True)

    per_day_fee = db.Column(db.Float, nullable=False)
    late_fee = db.Column(db.Float, nullable=False)

    book = db.relationship('Book', backref='borrow_detail')


class BorrowRequest(db.Model):
    __tablename__ = 'borrow_requests'

    id = db.Column(db.Integer, primary_key=True)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))

    status = db.Column(
        db.String(20),
        default='pending'
    )  # pending | approved | rejected | returned

    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.Date)

    borrower = db.relationship('User', backref='borrow_requests')
    book = db.relationship('Book', backref='borrow_requests')


# ================= BARTER =================
class BarterRequest(db.Model):
    __tablename__ = 'barter_requests'
    id = db.Column(db.Integer, primary_key=True)
    
    # FIX: Use 'books.id' (plural) to match your Book table definition
    requested_book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    
    # FIX: Use 'users.id' (plural) to match your User table definition
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    offered_book_title = db.Column(db.String(200), nullable=False)
    offered_book_author = db.Column(db.String(200), nullable=True) 
    offered_book_image = db.Column(db.String(200), nullable=True)
    
    offered_book_genre = db.Column(db.String(100))
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

class BarterDetail(db.Model):
    __tablename__ = 'barter_details'

    id = db.Column(db.Integer, primary_key=True)
    # FIX: Matches 'barter_requests.id' correctly now
    barter_request_id = db.Column(db.Integer, db.ForeignKey('barter_requests.id'), nullable=False)
    completed_at = db.Column(db.DateTime)

    barter_request = db.relationship('BarterRequest', backref='detail')