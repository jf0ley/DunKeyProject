import os
from flask import Blueprint, jsonify, request, redirect, flash, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from flask_jwt_extended import create_access_token
from . import db
from .model import User
from .validation import sanitize_username, is_valid_email, is_strong_password
from werkzeug.security import generate_password_hash, check_password_hash
from .logging_utils import log_login_failed, log_login_success, log_register

# Frontend path
FE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'frontend')

auth_bp = Blueprint('auth_blueprint', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/dashboard.html')
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        dob = request.form.get('date_of_birth', '').strip()

        # Validation
        if not username or not email or not password:
            message = 'All fields are required'
            if request.headers.get('Accept') == 'application/json':
                return jsonify(success=False, message=message), 400
            flash(message, 'error')
            return redirect('/register.html')
        
        if password != confirm:
            message = 'Passwords do not match'
            if request.headers.get('Accept') == 'application/json':
                return jsonify(success=False, message=message), 400
            flash(message, 'error')
            return redirect('/register.html')
        
        if User.query.filter_by(username=username).first():
            message = 'Username already taken'
            if request.headers.get('Accept') == 'application/json':
                return jsonify(success=False, message=message), 400
            flash(message, 'error')
            return redirect('/register.html')
        
        if User.query.filter_by(email=email).first():
            message = 'Email already registered'
            if request.headers.get('Accept') == 'application/json':
                return jsonify(success=False, message=message), 400
            flash(message, 'error')
            return redirect('/register.html')

        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        login_user(user)

        # JSON or HTML response
        if request.headers.get('Accept') == 'application/json':
            return jsonify(success=True, redirect_url='/dashboard.html'), 200

        flash('Registration successful!', 'success')
        return redirect('/dashboard.html')

    # Serve register form
    return send_from_directory(FE, 'register.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/dashboard.html')
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        message = 'Invalid username or password'
        if request.headers.get('Accept') == 'application/json':
            return jsonify(success=False, message=message), 401
        flash(message, 'error')
        return redirect('/login.html')
    
    login_user(user)

    if request.headers.get('Accept') == 'application/json':
        return jsonify(success=True, redirect_url='/dashboard.html', access_token='example-token'), 200

    flash('Logged in successfully!', 'success')
    return redirect('/dashboard.html')

# --- Logout Route ---
@auth_bp.route('/logout')
def logout():
    logout_user()
    return send_from_directory(FE, 'login.html')