from flask import Blueprint
ratings = Blueprint('ratings', __name__, template_folder='templates')
from . import routes
