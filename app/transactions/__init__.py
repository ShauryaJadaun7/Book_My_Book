from flask import Blueprint
transactions = Blueprint('transactions', __name__, template_folder='templates')
from . import routes
