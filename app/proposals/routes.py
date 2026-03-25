from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import proposals
from .forms import ProposalForm
from .services import create_proposal, respond_proposal
from ..models import Proposal, Book

@proposals.route('/propose/<int:book_id>', methods=['POST'])
@login_required
def propose(book_id):
    offered_book_id = request.form.get('offered_book_id')
    offered_cash = request.form.get('offered_cash', 0.0)
    message = request.form.get('message', '')

    if offered_book_id: offered_book_id = int(offered_book_id)
    if offered_cash: offered_cash = float(offered_cash)

    success, msg = create_proposal(
        current_user.id, 
        book_id, 
        offered_cash, 
        message,
        offered_book_id
    )
    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(url_for('books.detail', book_id=book_id))

@proposals.route('/incoming')
@login_required
def incoming():
    items = Proposal.query.filter_by(owner_id=current_user.id, status='PENDING').all()
    return render_template('proposals/incoming.html', proposals=items)

@proposals.route('/respond/<int:proposal_id>/<action>', methods=['POST'])
@login_required
def respond(proposal_id, action):
    success, msg = respond_proposal(proposal_id, current_user.id, action.upper())
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('proposals.incoming'))
