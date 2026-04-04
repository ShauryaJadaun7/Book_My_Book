from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from . import admin_bp
from ..models import PaymentRequest, SystemConfig, User, Book
from ..extensions import db
from datetime import datetime, timedelta, timezone

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            flash("You do not have permission to access that page.", "danger")
            return redirect(url_for('core.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@admin_required
def dashboard():
    pending_payments = PaymentRequest.query.filter_by(status='pending').order_by(PaymentRequest.created_at.desc()).all()
    
    # Get custom configs for pricing
    booster = db.session.get(SystemConfig, 'booster_price')
    scholar = db.session.get(SystemConfig, 'scholar_price')
    prices = {
        'booster': float(booster.value) if booster else 9.0,
        'scholar': float(scholar.value) if scholar else 19.0
    }
    # Fetch all platform inventory
    all_books = Book.query.order_by(Book.created_at.desc()).all()
    
    return render_template('admin/dashboard.html', requests=pending_payments, prices=prices, all_books=all_books)


@admin_bp.route('/approve/<int:pr_id>', methods=['POST'])
@admin_required
def approve_payment(pr_id):
    pr = db.session.get(PaymentRequest, pr_id)
    if not pr or pr.status != 'pending':
        flash("Invalid request.", "danger")
        return redirect(url_for('admin.dashboard'))
        
    pr.status = 'approved'
    user = pr.user
    
    if pr.requested_tier == 'scholar':
        user.tier = 'scholar'
        if user.scholar_credits is None:
            user.scholar_credits = 0
        user.scholar_credits += 1
        
    elif pr.requested_tier == 'booster' and pr.book_id:
        # Boost specific book
        book = db.session.get(Book, pr.book_id)
        if book:
            book.is_boosted = True
            # Extend expiry by 7 full days from right now
            book.expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    db.session.commit()
    flash(f"Approved UTR {pr.utr} for User {user.email}", "success")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/reject/<int:pr_id>', methods=['POST'])
@admin_required
def reject_payment(pr_id):
    pr = db.session.get(PaymentRequest, pr_id)
    if pr:
        pr.status = 'rejected'
        db.session.commit()
        flash(f"Rejected UTR {pr.utr}.", "info")
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/configure', methods=['POST'])
@admin_required
def update_pricing():
    new_booster = request.form.get('booster_price')
    new_scholar = request.form.get('scholar_price')
    
    def upsert_config(key, val, desc):
        cfg = db.session.get(SystemConfig, key)
        if not cfg:
            cfg = SystemConfig(key=key, description=desc)
            db.session.add(cfg)
        cfg.value = val

    if new_booster:
        upsert_config('booster_price', new_booster, "Price for 7-day single book Boost")
    if new_scholar:
        upsert_config('scholar_price', new_scholar, "Price for permanent Scholar limit upgrade")
        
    db.session.commit()
    flash("Pricing configurations updated successfully.", "success")
    return redirect(url_for('admin.dashboard'))
