from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from . import cart
from .services import add_to_cart, remove_from_cart, get_cart_items

@cart.route('/')
@login_required
def view_cart():
    items = get_cart_items(current_user.id)
    total = sum(item.book.price for item in items if item.book.price)
    return render_template('cart/index.html', items=items, total=total)

@cart.route('/add/<int:book_id>', methods=['POST'])
@login_required
def add(book_id):
    import json
    from flask import make_response
    success, msg = add_to_cart(current_user.id, book_id)
    
    if request.headers.get('HX-Request'):
        response = make_response("", 200)
        response.headers['HX-Trigger'] = json.dumps({
            "cartUpdated": {"value": msg, "type": "success" if success else "danger"}
        })
        return response

    if success:
        flash(msg, 'success')
    else:
        flash(msg, 'danger')
    return redirect(request.referrer or url_for('books.index'))

@cart.route('/remove/<int:book_id>', methods=['POST'])
@login_required
def remove(book_id):
    remove_from_cart(current_user.id, book_id)
    
    if request.headers.get('HX-Request'):
        import json
        from flask import make_response
        items = get_cart_items(current_user.id)
        new_total = sum(item.book.price for item in items if item.book.price)
        response = make_response("", 200)
        response.headers['HX-Trigger'] = json.dumps({
            "cartUpdated": {"value": "Item removed from cart.", "type": "warning"},
            "cartTotalUpdated": {"total": float(new_total), "count": len(items)}
        })
        return response

    flash("Item removed from cart.", "info")
    return redirect(url_for('cart.view_cart'))
