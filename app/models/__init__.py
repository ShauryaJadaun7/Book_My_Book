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

    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
