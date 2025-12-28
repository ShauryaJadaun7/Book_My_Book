from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from email_validator import validate_email, EmailNotValidError

from .models import User
from . import db

auth = Blueprint("auth", __name__)

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            email = validate_email(email).email
        except EmailNotValidError:
            flash("Invalid email address", "error")
            return redirect(url_for("auth.register"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "error")
            return redirect(url_for("auth.register"))
        
        if len(password) < 6:
            flash("Password must be at least 6 characters", "error")
            return redirect(url_for("auth.register"))

  
        new_user = User(
            email=email,
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        flash("Account created successfully", "success")
        return redirect(url_for("routes.home"))

    return render_template("register.html")



@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password", "error")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash("Logged in successfully", "success")
        return redirect(url_for("routes.home"))

    return render_template("login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "success")
    return redirect(url_for("auth.login"))
