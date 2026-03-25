from .celery_app import celery
from app import create_app
from app.extensions import mail
from flask_mail import Message

@celery.task
def send_async_email(subject, recipient, body):
    app = create_app('default')
    with app.app_context():
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        try:
            mail.send(msg)
            return "Email sent successfully"
        except Exception as e:
            return f"Failed to send email: {e}"
