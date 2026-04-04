from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import os

def college_email_check(form, field):
    domain_restriction = os.environ.get('COLLEGE_DOMAIN_RESTRICTION', '@adaniuni.ac.in')
    if domain_restriction and not field.data.lower().endswith(domain_restriction):
        raise ValidationError(f'Email must belong to {domain_restriction}')

class RegisterEmailForm(FlaskForm):
    full_name = StringField('Username (Full Name)', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('College Email', validators=[DataRequired(), Email(), college_email_check])
    phone = StringField('Phone Number (10 Digits)', validators=[DataRequired(), Length(min=10, max=10, message="Please enter exactly 10 digits.")])
    submit = SubmitField('Send OTP')

class OTPForm(FlaskForm):
    otp = StringField('6-Digit OTP', validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField('Verify')

class SetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Set Password & Login')
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class UpdateProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    phone = StringField('Phone Number (10 Digits)', validators=[Length(min=10, max=10, message="Please enter exactly 10 digits.")])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField('Confirm New', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

