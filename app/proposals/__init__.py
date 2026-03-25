from flask import Blueprint
proposals = Blueprint('proposals', __name__, template_folder='templates')
from . import routes
