from flask import Blueprint, request
from flask import render_template, redirect, url_for
from flask_login import current_user

routes = Blueprint('routes', __name__)

@routes.route('/')
def home():
    if current_user.is_authenticated:
        #give all books on  main page

        return redirect(url_for('routes.home'))
    
    return redirect(url_for('auth.register'))

@routes.route('/upload', methods=['GET', 'POST'])
def upload():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    if request.method == 'POST':
        img=request.files['image']

        # Handle file upload logic here
        pass
    return render_template('upload.html')

@routes.route('/mybooks')
def mybooks():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
        
    # Fetch books owned by the current user
    user_books = current_user.books 
    return render_template('mybooks.html', books=user_books)

@routes.route('/borrow_requests')
def borrow_requests():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Fetch borrow requests made by the current user
    user_borrow_requests = current_user.borrow_requests
    return render_template('borrow_requests.html', requests=user_borrow_requests)

@routes.route('/barter_requests')
def barter_requests():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Fetch barter requests made by the current user
    user_barter_requests = current_user.barter_requests
    return render_template('barter_requests.html', requests=user_barter_requests)
