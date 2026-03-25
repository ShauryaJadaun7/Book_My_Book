from ..extensions import db
from flask_login import UserMixin
from datetime import datetime, timezone

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable initially during OTP
    phone = db.Column(db.String(20), nullable=True)
    upi_id = db.Column(db.String(100), nullable=True)
    
    # Rating system
    average_rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    books = db.relationship('Book', backref='owner', lazy='dynamic')

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Eligibility flags
    is_for_sale = db.Column(db.Boolean, default=False)
    price = db.Column(db.Float, nullable=True)
    
    is_for_borrow = db.Column(db.Boolean, default=False)
    borrow_fee_per_day = db.Column(db.Float, nullable=True)
    
    is_for_barter = db.Column(db.Boolean, default=False)
    barter_preferences = db.Column(db.Text, nullable=True) # e.g. "Specific book title or sci-fi"

    # Seller's UPI ID for direct payment — required when is_for_sale or is_for_borrow
    upi_id = db.Column(db.String(100), nullable=True)

    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    book = db.relationship('Book', backref='cart_items')
    user = db.relationship('User', backref='cart_items')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    tx_type = db.Column(db.String(20), nullable=False) # 'SALE', 'BORROW', 'LATE_FEE'
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)

    # Status lifecycle:
    # PENDING → AWAITING_SELLER_CONFIRMATION → COMPLETED
    #                                         → DISPUTED  (48-hr timeout)
    # FAILED stays terminal
    status = db.Column(db.String(50), default='PENDING')

    # UPI-specific fields
    upi_ref             = db.Column(db.String(100), nullable=True)  # UTR / ref number from buyer
    buyer_confirmed_at  = db.Column(db.DateTime,    nullable=True)  # when buyer clicked "I've Paid"
    seller_confirmed_at = db.Column(db.DateTime,    nullable=True)  # when seller clicked "Received"

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships for convenient access in templates
    buyer  = db.relationship('User', foreign_keys=[buyer_id],  backref='purchases')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sales')
    book   = db.relationship('Book', foreign_keys=[book_id],   backref='transactions')

class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    status = db.Column(db.String(50), default='REQUESTED') # REQUESTED, APPROVED, REJECTED, ACTIVE, RETURNED
    
    requested_days = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    returned_date = db.Column(db.DateTime, nullable=True)
    
    late_fee_accrued = db.Column(db.Float, default=0.0)

class Proposal(db.Model):
    __tablename__ = 'proposals'
    id = db.Column(db.Integer, primary_key=True)
    target_book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    offered_book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=True)
    offered_cash = db.Column(db.Float, default=0.0)
    message = db.Column(db.Text, nullable=True)
    
    status = db.Column(db.String(50), default='PENDING') # PENDING, ACCEPTED, REJECTED

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True)
    borrow_record_id = db.Column(db.Integer, db.ForeignKey('borrow_records.id'), nullable=True)
    
    stars = db.Column(db.Integer, nullable=False) # 1 to 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Links the notification to a specific request so accept/reject can be
    # handled directly from the notifications page.
    ref_type = db.Column(db.String(20), nullable=True)   # 'BORROW' | 'BARTER'
    ref_id   = db.Column(db.Integer,    nullable=True)   # BorrowRecord.id or Proposal.id
    actionable = db.Column(db.Boolean,  default=False)   # show accept/reject buttons

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
