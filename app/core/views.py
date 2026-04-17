from flask import render_template, redirect, url_for
from . import core

from flask_login import current_user

@core.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('landing.html')
    return redirect(url_for('books.index'))
