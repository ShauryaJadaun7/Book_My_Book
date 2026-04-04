from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

class UTRForm(FlaskForm):
    utr = StringField('12-Digit UTR Number', validators=[
        DataRequired(),
        Length(min=12, max=12, message="UTR must be exactly 12 digits long"),
        Regexp(r'^[0-9A-Za-z]+$', message="UTR must be alphanumeric")
    ])
    submit = SubmitField('Confirm Payment')
