from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from . import payments_bp
from .forms import UTRForm
from ..models import PaymentRequest, SystemConfig, Book
from ..extensions import db
import datetime

def get_pricing():
    booster = db.session.get(SystemConfig, 'booster_price')
    scholar = db.session.get(SystemConfig, 'scholar_price')
    
    return {
        'booster': float(booster.value) if booster else 9.0,
        'scholar': float(scholar.value) if scholar else 19.0
    }

@payments_bp.route('/pricing')
def pricing():
    prices = get_pricing()
    return render_template('payments/pricing.html', prices=prices)

@payments_bp.route('/checkout/<tier>', methods=['GET', 'POST'])
@login_required
def checkout(tier):
    if tier not in ['booster', 'scholar']:
        flash("Invalid tier selected.", "danger")
        return redirect(url_for('payments.pricing'))

    prices = get_pricing()
    price = prices.get(tier)

    # Optional: If picking booster, which book?
    book_id_req = request.args.get('book_id', type=int)

    # Simple Redis Rate limit to block brute-force UTR attempts (3 tries / 15 mins)
    import redis
    redis_url = current_app.config.get('REDIS_URL', 'redis://localhost:6379/1')
    try:
        r = redis.from_url(redis_url)
        attempts = r.get(f"utr_attempts:{current_user.id}")
        if attempts and int(attempts) >= 3:
            flash("You have submitted too many UTRs recently. Please wait 15 minutes.", "danger")
            return redirect(url_for('core.index'))
    except Exception as e:
        r = None # Graceful failure if Redis is down

    form = UTRForm()
    if form.validate_on_submit():
        utr = form.utr.data
        
        # Check if already used
        existing = PaymentRequest.query.filter_by(utr=utr).first()
        if existing:
            if r:
                r.incr(f"utr_attempts:{current_user.id}")
                r.expire(f"utr_attempts:{current_user.id}", 900)
            flash("This UTR has already been submitted or is invalid.", "danger")
            return redirect(request.url)
            
        pr = PaymentRequest(
            user_id=current_user.id,
            utr=utr,
            requested_tier=tier,
            book_id=book_id_req
        )
        db.session.add(pr)
        db.session.commit()
        
        flash("We have received your payment request! An admin will verify the UTR shortly.", "success")
        return redirect(url_for('core.index'))

    return render_template('payments/checkout.html', form=form, tier=tier, price=price, book_id=book_id_req)
