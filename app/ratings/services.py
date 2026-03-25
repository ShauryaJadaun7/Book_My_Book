from ..extensions import db
from ..models import Rating, User

def add_rating(reviewer_id, reviewee_id, transaction_id, stars, comment):
    rating = Rating(
        reviewer_id=reviewer_id,
        reviewee_id=reviewee_id,
        transaction_id=transaction_id,
        stars=stars,
        comment=comment
    )
    db.session.add(rating)
    
    # Update user average
    reviewee = db.session.get(User, reviewee_id)
    if reviewee:
        total_stars = (reviewee.average_rating * reviewee.rating_count) + stars
        reviewee.rating_count += 1
        reviewee.average_rating = total_stars / reviewee.rating_count
        
    db.session.commit()
    return True, "Rating submitted successfully."
