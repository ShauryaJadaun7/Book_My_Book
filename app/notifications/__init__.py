from flask import Blueprint
notifications = Blueprint('notifications', __name__, template_folder='templates')
from . import routes
