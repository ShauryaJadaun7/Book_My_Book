from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from . import auth
from .forms import RegisterEmailForm, OTPForm, LoginForm, UpdateProfileForm, ChangePasswordForm, SetPasswordForm
from .services import generate_and_send_otp, verify_otp, create_user_after_password, update_user_password, generate_random_password, send_password_email
from ..models import User
from ..extensions import login_manager, db

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    # If using test mode, auto redirect with default values
    form = RegisterEmailForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('Email already registered.', 'warning')
            return redirect(url_for('auth.login'))
            
        phone_data = form.phone.data
        if phone_data and not phone_data.startswith('+91'):
            phone_data = '+91' + phone_data
            
        success, msg = generate_and_send_otp(form.email.data, phone_data)
        if not success:
            flash(msg, 'danger')
            return redirect(url_for('auth.register'))
            
        session['reg_email'] = form.email.data
        session['reg_phone'] = phone_data
        session['reg_name'] = form.full_name.data
        return redirect(url_for('auth.verify_registration_otp'))
    return render_template('auth/register.html', form=form)

@auth.route('/register/otp', methods=['GET', 'POST'])
def verify_registration_otp():
    if 'reg_email' not in session:
        return redirect(url_for('auth.register'))
        
    form = OTPForm()
    if form.validate_on_submit():
        success, msg = verify_otp(session['reg_email'], form.otp.data)
        if success:
            session['otp_verified'] = True
            flash('Phone verified! Please set your secure password.', 'success')
            return redirect(url_for('auth.set_password'))
        else:
            flash(msg, 'danger')
    return render_template('auth/otp.html', form=form, email=session.get('reg_email'))

@auth.route('/register/password', methods=['GET', 'POST'])
def set_password():
    if not session.get('otp_verified') or 'reg_email' not in session:
        return redirect(url_for('auth.register'))
        
    form = SetPasswordForm()
    if form.validate_on_submit():
        email = session['reg_email']
        phone = session.get('reg_phone')
        name = session.get('reg_name', 'Student')
        password = form.password.data
        
        success, result = create_user_after_password(email, phone, name, password)
        if success:
            session.pop('reg_email', None)
            session.pop('reg_phone', None)
            session.pop('reg_name', None)
            session.pop('otp_verified', None)
            
            login_user(result)
            flash('Account created successfully! Welcome to BookMyBook.', 'success')
            return redirect(url_for('core.index'))
        else:
            flash(result, 'danger')
            return redirect(url_for('auth.register'))
            
    return render_template('auth/set_password.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password_hash and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('core.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('core.index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    
    form = UpdateProfileForm(obj=current_user)
    if request.method == 'GET' and form.phone.data and form.phone.data.startswith('+91'):
        form.phone.data = form.phone.data[3:]
        
    password_form = ChangePasswordForm()
    
    if form.submit.data and form.validate():
        current_user.full_name = form.full_name.data
        phone_data = form.phone.data
        if phone_data and not phone_data.startswith('+91'):
            phone_data = '+91' + phone_data
        current_user.phone = phone_data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('auth.profile'))
        
    if password_form.submit.data and password_form.validate():
        success, msg = update_user_password(current_user, password_form.old_password.data, password_form.new_password.data)
        if success:
            flash('Password changed successfully.', 'success')
        else:
            flash(msg, 'danger')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/profile.html', form=form, password_form=password_form)
