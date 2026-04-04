from wsgi import app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    email = "jadaun@gmail.com"
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            full_name="Shaurya Admin",
            phone="+910000000000",
            password_hash=generate_password_hash("admin123")
        )
        db.session.add(user)
    else:
        user.password_hash = generate_password_hash("admin123")
        
    user.is_admin = True
    user.tier = 'scholar' # Also give you scholar privileges!
    db.session.commit()
    print(f"Admin account established for {email}")
