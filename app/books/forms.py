from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional

class UploadBookForm(FlaskForm):
    title = StringField('Book Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    cover_image = FileField('Cover Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    
    # Eligibility
    is_for_sale = BooleanField('Available for Sale')
    price = FloatField('Sale Price (₹)', validators=[Optional()])
    
    is_for_borrow = BooleanField('Available for Borrowing')
    borrow_fee_per_day = FloatField('Borrow Fee Rate (₹/day)', validators=[Optional()])
    
    is_for_barter = BooleanField('Available for Barter')
    barter_preferences = TextAreaField('Barter Preferences (e.g. specific book title, or genre)', validators=[Optional()])

    apply_booster = BooleanField('✨ Boost this book to the top of the feed (₹9) - Optional', default=False)

    submit = SubmitField('Upload Book')
    
    def validate(self, extra_validators=None):
        initial_validation = super(UploadBookForm, self).validate()
        if not initial_validation:
            return False

        if not (self.is_for_sale.data or self.is_for_borrow.data or self.is_for_barter.data):
            self.is_for_sale.errors.append('Select at least one option: Sale, Borrow, or Barter.')
            return False

        if self.is_for_sale.data and not self.price.data:
            self.price.errors.append('Price is required for sale.')
            return False

        if self.is_for_borrow.data and not self.borrow_fee_per_day.data:
            self.borrow_fee_per_day.errors.append('Borrow fee rate is required.')
            return False

        return True
