from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import User

main = Blueprint('main', __name__)

@main.route('/')
def test():
    return render_template('home.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if the user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('main.register'))
        
        # Create a new user and add it to the database
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful, please log in.')
        return redirect(url_for('main.login'))
    return render_template('register.html')

@main.route('/login')
def login():
    return render_template('login.html')
