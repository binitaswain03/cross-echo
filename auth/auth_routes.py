from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from models.models import db, User, Settings

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        email_or_username = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter((User.email == email_or_username) | (User.username == email_or_username)).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('main.dashboard'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template('register.html')
            
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template('register.html')
            
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # Initialize default settings for user
        user_settings = Settings(user_id=new_user.id)
        db.session.add(user_settings)
        db.session.commit()
        
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))
