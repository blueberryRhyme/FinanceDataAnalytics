from flask import Blueprint, render_template, request, abort, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from . import db, bcrypt
from .models import User, Expense
from app.forms import ExpenseForm, RegistrationForm, LoginForm, LogoutForm
main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.profile'))
    return render_template('home6.html')

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
        expense = Expense(
            amount   = amount,
            category = category,
            date     = form.date.data,
            user_id  = current_user.id
        )
        db.session.add(expense)
        db.session.commit()

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



@main.route('/api/expenses')
@login_required
def api_expenses():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    return jsonify([e.to_dict() for e in expenses])

@main.route("/friends")
@login_required
def friends():
    return render_template("friends.html")


@main.route("/add_friend/<int:user_id>", methods=["POST"])
@login_required
def add_friend(user_id):
    if user_id == current_user.id:
        abort(400)

    other = User.query.get_or_404(user_id)
    if other not in current_user.friends:
        current_user.friends.append(other)
        db.session.commit()
        flash(f"{other.username} is now your friend!", "success")
    else:
        flash(f"You’re already friends with {other.username}.", "info")

    return redirect(url_for("main.friends"))

@main.route("/api/user_search")
@login_required
def api_user_search():
    q = request.args.get("q", "").strip()
    # base query: everyone except yourself
    query = User.query.filter(User.id != current_user.id)

    if q:
        query = query.filter(User.username.ilike(f"%{q}%"))

    # limit results to, say, 10 matches
    users = query.order_by(User.username).limit(10).all()

    return jsonify(
        [{"id": u.id, "username": u.username} for u in users]
    )