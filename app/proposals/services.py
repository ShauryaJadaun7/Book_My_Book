from ..extensions import db
from ..models import Proposal, Book, Notification, User


def create_proposal(requester_id, target_book_id, offered_cash, message, offered_book_id=None):
    target_book = db.session.get(Book, target_book_id)
    if not target_book or not target_book.is_for_barter:
        return False, "Book unavailable for barter."
    if not target_book.is_available:
        return False, "This book is currently unavailable."

    requester = db.session.get(User, requester_id)
    
    offered_book_title = "a book"
    if offered_book_id:
        offered_book = db.session.get(Book, offered_book_id)
        if offered_book:
            offered_book_title = f"'{offered_book.title}'"

    proposal = Proposal(
        target_book_id=target_book_id,
        requester_id=requester_id,
        owner_id=target_book.owner_id,
        offered_cash=offered_cash,
        message=message,
        offered_book_id=offered_book_id
    )
    db.session.add(proposal)
    db.session.flush()  # get proposal.id before commit

    cash_line = f"₹{offered_cash:.2f} cash + {offered_book_title}" if offered_cash else f"book swap with {offered_book_title} (no cash)"
    msg_line  = f"\n📝 Their note: \"{message}\"" if message else ""

    notif = Notification(
        user_id=target_book.owner_id,
        title="New Barter Proposal",
        message=(
            f"{requester.full_name or 'Someone'} wants to barter for your book "
            f"'{target_book.title}'.\n\n"
            f"📧 Email: {requester.email}\n"
            f"📞 Phone: {requester.phone or 'not provided'}\n"
            f"💵 Offer: {cash_line}{msg_line}\n\n"
            f"💰 Payment note: If you accept, coordinate payment directly with them."
        ),
        ref_type='BARTER',
        ref_id=proposal.id,
        actionable=True
    )
    db.session.add(notif)
    db.session.commit()
    return True, "Proposal sent successfully!"


def respond_proposal(proposal_id, owner_id, action):
    proposal = db.session.get(Proposal, proposal_id)
    if not proposal or proposal.owner_id != owner_id:
        return False, "Invalid proposal."

    # Mark the actionable notification as done
    notif = Notification.query.filter_by(ref_type='BARTER', ref_id=proposal_id, actionable=True).first()

    if action == 'ACCEPT':
        proposal.status = 'ACCEPTED'
        book = db.session.get(Book, proposal.target_book_id)
        if book:
            book.is_available = False

        owner = db.session.get(User, owner_id)

        # Notify requester — include owner contact + payment reminder
        db.session.add(Notification(
            user_id=proposal.requester_id,
            title="Barter Proposal Accepted ✅",
            message=(
                f"Your barter proposal for '{book.title if book else 'the book'}' was accepted!\n\n"
                f"📧 Owner email: {owner.email}\n"
                f"📞 Owner phone: {owner.phone or 'not provided'}\n\n"
                f"💰 Please coordinate payment and exchange directly with the owner."
            )
        ))

        if notif:
            notif.is_read = True
            notif.actionable = False

        db.session.commit()
        return True, "Proposal accepted."

    elif action == 'REJECT':
        proposal.status = 'REJECTED'
        book = db.session.get(Book, proposal.target_book_id)

        db.session.add(Notification(
            user_id=proposal.requester_id,
            title="Barter Proposal Rejected ❌",
            message=(
                f"Your barter proposal for '{book.title if book else 'the book'}' "
                f"was not accepted by the owner."
            )
        ))

        if notif:
            notif.is_read = True
            notif.actionable = False

        db.session.commit()
        return True, "Proposal rejected."

    return False, "Invalid action."
