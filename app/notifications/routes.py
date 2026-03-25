from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import notifications
from ..extensions import db
from ..models import Notification


@notifications.route('/')
@login_required
def index():
    notifs = (
        Notification.query
        .filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template('notifications/index.html', notifications=notifs)


@notifications.route('/read/<int:notif_id>', methods=['POST'])
@login_required
def mark_read(notif_id):
    notif = db.session.get(Notification, notif_id)
    if notif and notif.user_id == current_user.id:
        notif.is_read = True
        db.session.commit()
    return redirect(request.referrer or url_for('notifications.index'))


@notifications.route('/respond/<int:notif_id>/<action>', methods=['POST'])
@login_required
def respond(notif_id, action):
    """
    Single handler for accepting / rejecting borrow requests and barter proposals
    directly from the notifications page.
    action — 'accept' or 'reject'
    """
    notif = db.session.get(Notification, notif_id)
    if not notif or notif.user_id != current_user.id or not notif.actionable:
        flash("Notification not found or already responded.", "danger")
        return redirect(url_for('notifications.index'))

    action_upper = action.upper()  # 'ACCEPT' / 'REJECT'

    if notif.ref_type == 'BORROW':
        from ..borrows.services import respond_borrow
        # Map ACCEPT → APPROVE to match existing service vocabulary
        borrow_action = 'APPROVE' if action_upper == 'ACCEPT' else 'REJECT'
        success, msg = respond_borrow(notif.ref_id, current_user.id, borrow_action)
        flash(msg, 'success' if success else 'danger')

    elif notif.ref_type == 'BARTER':
        from ..proposals.services import respond_proposal
        success, msg = respond_proposal(notif.ref_id, current_user.id, action_upper)
        flash(msg, 'success' if success else 'danger')

    else:
        flash("Unknown request type.", "danger")

    return redirect(url_for('notifications.index'))
