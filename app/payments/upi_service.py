import io
try:
    import qrcode
except ImportError:
    qrcode = None

from datetime import datetime, timezone
from flask import current_app, render_template
from ..extensions import db, mail
from flask_mail import Message
from ..models import Transaction, Book, Notification, User

def generate_upi_qr(upi_id, amount, note):
    """
    Generates a UPI deep-link QR code for the given UPI ID and amount.
    Returns the QR code as a PNG byte array.
    """
    if qrcode is None:
        raise Exception("The 'qrcode' library is not installed. Run: pip install qrcode[pil]")
        
    # Create an upi://pay URI
    # format: upi://pay?pa=UPIID&pn=Name&am=Amount&cu=INR&tn=Note
    uri = f"upi://pay?pa={upi_id}&pn=BookMyBook&am={amount:.2f}&cu=INR&tn={note}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save image to byte stream
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return img_io.getvalue()

def send_payment_email(to_email, subject, body):
    msg = Message(subject=subject,
                  sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
                  recipients=[to_email],
                  body=body)
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")

def buyer_confirm(tx_id, buyer_id, upi_ref):
    tx = db.session.get(Transaction, tx_id)
    if not tx or tx.buyer_id != buyer_id or tx.status != 'PENDING':
        return False, "Invalid transaction or already confirmed."
    
    tx.upi_ref = upi_ref
    tx.status = 'AWAITING_SELLER_CONFIRMATION'
    tx.buyer_confirmed_at = datetime.now(timezone.utc)
    
    book = db.session.get(Book, tx.book_id)
    seller = db.session.get(User, tx.seller_id)
    buyer = db.session.get(User, buyer_id)
    
    # Send in-app notification
    notif = Notification(
        user_id=seller.id,
        title="Payment Confirmation Pending",
        message=(f"Buyer {buyer.full_name or buyer.email} claims to have paid ₹{tx.amount:.2f} "
                 f"for '{book.title}' via UPI. Ref/UTR: {upi_ref or 'Not provided'}.\n"
                 f"Please verify in your UPI app and mark as received.")
    )
    db.session.add(notif)
    db.session.commit()
    
    # Send email
    body = (f"Hello {seller.full_name or seller.email},\n\n"
            f"Buyer {buyer.full_name or buyer.email} claims payment is done for '{book.title}' "
            f"(Amount: ₹{tx.amount:.2f}).\n"
            f"UPI Ref/UTR: {upi_ref or 'Not provided'}\n\n"
            f"Please check your bank/UPI app and mark this transaction as received in BookMyBook.\n")
    send_payment_email(seller.email, "Verify Payment - BookMyBook", body)
    
    return True, "Payment confirmation sent! Seller will verify soon."

def seller_confirm(tx_id, seller_id):
    tx = db.session.get(Transaction, tx_id)
    if not tx or tx.seller_id != seller_id or tx.status != 'AWAITING_SELLER_CONFIRMATION':
        return False, "Invalid transaction."
    
    tx.status = 'COMPLETED'
    tx.seller_confirmed_at = datetime.now(timezone.utc)
    
    book = db.session.get(Book, tx.book_id)
    buyer = db.session.get(User, tx.buyer_id)
    seller = db.session.get(User, seller_id)
    
    if book:
        book.is_available = False # Mark as sold/unavailable
    
    # Send in-app notification
    notif = Notification(
        user_id=buyer.id,
        title="Payment Received ✅",
        message=(f"Seller {seller.full_name or seller.email} confirmed receiving your "
                 f"payment of ₹{tx.amount:.2f} for '{book.title}'.\n"
                 f"You can now contact them to collect the book.\n"
                 f"📧 Email: {seller.email}\n"
                 f"📞 Phone: {seller.phone or 'not provided'}")
    )
    db.session.add(notif)
    db.session.commit()
    
    # Send email to buyer
    body = (f"Hello {buyer.full_name or buyer.email},\n\n"
            f"The seller has confirmed your payment of ₹{tx.amount:.2f} for '{book.title}'.\n"
            f"Here are the seller's contact details to arrange pickup/delivery:\n"
            f"Name: {seller.full_name or 'N/A'}\n"
            f"Email: {seller.email}\n"
            f"Phone: {seller.phone or 'N/A'}\n\n"
            f"Thank you for using BookMyBook!")
    send_payment_email(buyer.email, "Payment Confirmed - BookMyBook", body)
    
    return True, "Payment marked received. Buyer notified."
