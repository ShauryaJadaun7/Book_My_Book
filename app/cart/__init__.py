from flask import Blueprint
cart = Blueprint('cart', __name__, template_folder='templates')
from . import routes
