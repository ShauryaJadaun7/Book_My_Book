from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import ratings
from .services import add_rating
from ..models import User

@ratings.route('/rate/<int:user_id>', methods=['GET', 'POST'])
@login_required
def rate(user_id):
    target_user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        stars = int(request.form.get('stars', 5))
        comment = request.form.get('comment', '')
        tx_id = request.form.get('transaction_id')
        
        add_rating(current_user.id, target_user.id, tx_id, stars, comment)
        flash("Thanks for rating!", "success")
        return redirect(url_for('core.index'))
        
    return render_template('ratings/rate.html', target_user=target_user)
