from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from . import db, bcrypt
from .models import User
from app.forms import ExpenseForm, RegistrationForm, LoginForm, LogoutForm
main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.profile'))
    return render_template('home6.html')

@main.route('/exp1')
@login_required
def exp1():
    # You could fetch expenses here or use JavaScript to load them
    return render_template('exp1.html')

@main.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # hash the password
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=pw_hash)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.expenseForm'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # look up the user
        user = User.query.filter_by(email=form.email.data).first()
        # verify password
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            #  TODO: redirect to main profile page 
            return redirect(url_for('main.expenseForm'))
        flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html', form=form)


@main.route('/profile')
@login_required
def profile():
    logout_form = LogoutForm()
    return render_template('profile.html',logout_form=logout_form)



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

        # then redirect with params in the URL
        return redirect(url_for('main.submission', 
                                amount=amount,
                                category=category,
                                date=date))

    return render_template('expenseForm.html', form=form)


@main.route('/submission', methods=['GET'])
def submission():
    amount   = request.args.get('amount')
    category = request.args.get('category')
    date     = request.args.get('date')

    if category == 'other':
        custom = request.form.get('otherCategory', '').strip()
        if custom:
            category = custom

    return render_template('submission.html',amount=amount,category=category,date=date)

@main.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))