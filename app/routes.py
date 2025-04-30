import csv
from collections import defaultdict
from io import TextIOWrapper
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
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
            return redirect(url_for('main.profile'))
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

    csv_file = request.files.get('csv_file')
    if csv_file and csv_file.filename.lower().endswith('.csv'):
        stream = TextIOWrapper(csv_file.stream, encoding='utf-8-sig')
        reader = csv.DictReader(stream)
        fieldnames = reader.fieldnames or []

        # required columns:
        required = ['date', 'amount', 'description', 'balance']
        mapping = {}
        missing = []


        for key in required:
            for h in fieldnames:
                if key in h.strip().lower():
                    mapping[key] = h
                    break
            else:
                missing.append(key)

        if missing:
            flash(f"CSV is missing required columns: {', '.join(missing)}", "danger")
            return redirect(request.url)

        # Now process rows using mapping[key] to pull the right column
        for row in reader:
            try:
                dt_raw   = row[mapping['date']].strip()
                amt_raw  = row[mapping['amount']].strip().replace(',', '')
                desc_raw = row[mapping['description']].strip()
                bal_raw  = row[mapping['balance']].strip().replace(',', '')

                amt = float(amt_raw)
                bal = float(bal_raw)
            except Exception as e:
                current_app.logger.warning(f"Skipping bad row {reader.line_num}: {e}")
                continue

            expense = Expense(
                user_id    = current_user.id,
                date       = dt_raw,
                amount     = amt,
                # TODO: improve this / use external lib
                category   = categorize_by_vendor(desc_raw) or 'Uncategorized'
            )
            db.session.add(expense)

        db.session.commit()
        flash("CSV uploaded and expenses recorded!", "success")
        return redirect(url_for('main.submission', 
                                amount=expense.amount,
                                category=expense.category,
                                date=expense.date))

    if form.validate_on_submit():
        amount = float(form.amount.data)
        category = form.category.data
        if category == 'other':
            category = form.other_category.data.strip() or 'Other'
        date = form.date.data.isoformat()

        # save to database here
        expense = Expense(
            user_id    = current_user.id,
            amount   = amount,
            category = category,
            date     = form.date.data,
        )
        db.session.add(expense)
        db.session.commit()


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

@main.route('/friends')
@login_required
def friends():
    logout_form = LogoutForm()
    return render_template('friends.html', logout_form=logout_form)



#   grouped by category
@main.route('/api/expenses')
@login_required
def api_expenses():
    rows = (Expense.query
            .filter_by(user_id=current_user.id)
            .order_by(Expense.date)
            .all())

    grouped = defaultdict(list)
    for e in rows:
        grouped[e.category].append({
            'date':   e.date.isoformat(),
            'amount': e.amount
        })

    #  list of category objects
    data = []
    for category, items in grouped.items():
        # the last 100 entries:
        items = items[-100:]
        data.append({
            'category': category,
            'history':  items
        })

    return jsonify(data)

VENDOR_MAP = {
    "woolworth": "Groceries",
    "coles":      "Groceries",
    "uber":       "Transport",
    "shell":      "Fuel",
    "netflix":    "Entertainment",
    "balthazar":  "restaurant",
    "Interest":   "Interest",
    "Savings":   "Savings",
}

def categorize_by_vendor(desc: str):
    text = desc.lower()
    for vendor, cat in VENDOR_MAP.items():
        if vendor in text:
            return cat
    return None