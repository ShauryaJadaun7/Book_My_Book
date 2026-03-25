from flask import Blueprint
payments = Blueprint('payments', __name__, template_folder='templates')
from . import routes
