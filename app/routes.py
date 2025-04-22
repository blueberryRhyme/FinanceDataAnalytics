from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import db
from .models import User
from app.forms import ExpenseForm
main = Blueprint('main', __name__)

@main.route('/')
def home():
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


@main.route('/expenseForm', methods=['GET', 'POST'])
def expenseForm():
    form = ExpenseForm()
    if form.validate_on_submit():
        amount = float(form.amount.data)
        category = form.category.data
        if category == 'other':
            category = form.other_category.data.strip() or 'Other'
        date = form.date.data.isoformat()

        # save to database here …

    return render_template('expenseForm.html', form=form)


@main.route('/submission', methods=['POST'])
def submission():
    amount   = request.form.get('amount')
    category = request.form.get('category')
    date     = request.form.get('date')

    if category == 'other':
        custom = request.form.get('otherCategory', '').strip()
        if custom:
            category = custom

    return render_template('submission.html',amount=amount,category=category,date=date)

