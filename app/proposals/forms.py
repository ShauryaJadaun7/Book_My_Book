from flask_wtf import FlaskForm
from wtforms import FloatField, TextAreaField, SubmitField
from wtforms.validators import Optional

class ProposalForm(FlaskForm):
    offered_cash = FloatField('Additional Cash Offered (₹)', validators=[Optional()])
    message = TextAreaField('Message/Preferred Book details', validators=[Optional()])
    submit = SubmitField('Send Proposal')
