from flask import Blueprint
borrows = Blueprint('borrows', __name__, template_folder='templates')
from . import routes
