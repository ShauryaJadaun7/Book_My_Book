from flask import Blueprint

core = Blueprint('core', __name__)

from . import errors, jinja_filters, views
