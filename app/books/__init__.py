from flask import Blueprint

books = Blueprint('books', __name__, template_folder='templates')

from . import routes
