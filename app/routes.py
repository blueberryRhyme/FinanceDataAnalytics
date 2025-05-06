import csv
import re
from collections import defaultdict
from io import TextIOWrapper
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from . import db, bcrypt
from .models import User, UserSettings, Transaction
from app.forms import TransactionForm, RegistrationForm, LoginForm, LogoutForm
from datetime import datetime,date, timedelta

from sqlalchemy import func, extract

main = Blueprint('main', __name__)

@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.profile'))
    return render_template('home6.html')

@main.route('/dashboard')
@login_required
def dashboard():

    today = date.today()
    ym_this = (today.year, today.month)
    last_month_date = (today.replace(day=1) - timedelta(days=1))
    ym_last = (last_month_date.year, last_month_date.month)

    # 1) TOTAL EXPENSES
    total_exp_this  = sum_category(None, *ym_this, tx_type="expense")   # pass None to mean “all categories”
    total_exp_last  = sum_category(None, *ym_last, tx_type="expense")
    exp_pct_change  = ((total_exp_this - total_exp_last) / total_exp_last * 100) \
                        if total_exp_last else 0

    # 2) SAVINGS CATEGORY
    savings_this = sum_category('savings', *ym_this, tx_type='income')
    savings_last = sum_category('savings', *ym_last, tx_type='income')
    sav_pct_change = ((savings_this - savings_last) / savings_last * 100) if savings_last else 0
    #   DEBUG
    print(f'saving: {savings_this} and {sav_pct_change}')


    # 3) BUDGET 

    if current_user.settings is None:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()
    else:
        settings = current_user.settings

    budget = settings.monthly_budget

    budget = current_user.settings.monthly_budget
    remaining = budget - total_exp_this
    rem_pct   = (remaining / budget * 100) if budget else 0

    return render_template('dashboard.html',
        total_expenses       = round(total_exp_this, 2),
        exp_pct_change       = round(exp_pct_change, 1),
        savings              = round(savings_this, 2),
        sav_pct_change       = round(sav_pct_change, 1),
        budget               = round(budget, 2),
        rem_pct              = round(rem_pct, 1),
    )

@main.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # hash the password
        pw_hash = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=pw_hash)
        user.settings = UserSettings()
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.transactionForm'))
    
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



@main.route('/transactionForm', methods=['GET', 'POST'])
@login_required
def transactionForm():
    form = TransactionForm()

    # --- CSV import path ---
    csv_file = request.files.get('csv_file')
    if csv_file and csv_file.filename.lower().endswith('.csv'):
        stream    = TextIOWrapper(csv_file.stream, encoding='utf-8-sig')
        reader    = csv.DictReader(stream)
        headers   = reader.fieldnames or []

        # build a mapping from logical keys to the actual header text
        required  = ['date', 'amount', 'description']
        mapping   = {}
        missing   = []
        for key in required:
            for h in headers:
                if key in h.strip().lower():
                    mapping[key] = h
                    break
            else:
                missing.append(key)

        if missing:
            flash(f"CSV is missing required columns: {', '.join(missing)}", "danger")
            return redirect(request.url)

        added   = 0
        # now iterate using the real header names
        for row in reader:
            dt_raw  = row[mapping['date']].strip()
            amt_raw = row[mapping['amount']].strip().replace(',', '')
            desc    = row[mapping['description']].strip()

            # parse date DD/MM/YYYY
            try:
                dt_obj = datetime.strptime(dt_raw, "%d/%m/%Y").date()
            except ValueError:
                current_app.logger.warning(f"Row {reader.line_num} bad date: {dt_raw}")
                continue

            # parse amount (keep sign)
            try:
                amt = float(amt_raw)
            except ValueError:
                current_app.logger.warning(f"Row {reader.line_num} bad amount: {amt_raw}")
                continue

            # determine tx_type + category + direction
            if 'transfer' in desc.lower():
                tx_type  = 'transfer'
                direction= 'in' if amt >= 0 else 'out'
                amt      = abs(amt)
                cat      = f"Transfer ({'In' if direction=='in' else 'Out'})"
            else:
                direction = None
                if amt >= 0:
                    tx_type = 'income'
                    cat     = 'Income'
                else:
                    tx_type = 'expense'
                    amt     = abs(amt)
                    cat     = categorize_by_vendor(desc) or 'Uncategorized'

            tx = Transaction(
                user_id            = current_user.id,
                date               = dt_obj,
                amount             = amt,
                category           = cat,
                description        = desc,
                type               = tx_type,
                transfer_direction = direction
            )
            db.session.add(tx)
            added += 1

        db.session.commit()

        flash(f"{added} transactions imported from CSV", "success")
        return redirect(url_for('main.submission', count=added))

    # --- Manual form path ---
    if form.validate_on_submit():
        tx_type  = form.type.data
        amt       = float(form.amount.data)
        dt        = form.date.data
        desc      = form.description.data.strip()

        # build category (with "other" override)
        if form.category.data == 'other':
            cat = form.other_category.data.strip()
        else:
            cat = form.category.data

        # for transfers, use transfer_direction
        direction = None
        if tx_type == 'transfer':
            direction = form.transfer_direction.data
            cat = f"Transfer ({'In' if direction=='in' else 'Out'})"

        tx = Transaction(
            user_id            = current_user.id,
            date               = dt,
            amount             = abs(amt),
            category           = cat,
            type               = tx_type,
            description        = desc,
            transfer_direction = direction
        )
        db.session.add(tx)
        db.session.commit()

        flash("Transaction recorded!", "success")
        return redirect(url_for(
            'main.submission',
            amount   = tx.amount,
            category = tx.category,
            date     = tx.date.isoformat(),
            tx_type  = tx.type
        ))

    return render_template('transactionForm.html', form=form)


@main.route('/transactions', methods=['GET', 'POST'])
@login_required
def transactions():
    if request.method == 'POST':
        # Handle updates or deletions
        action = request.form.get('action')
        transaction_id = request.form.get('transaction_id')

        if action == 'delete':
            # Delete the transaction
            tx = Transaction.query.get(transaction_id)
            if tx and tx.user_id == current_user.id:
                db.session.delete(tx)
                db.session.commit()
                flash('Transaction deleted successfully.', 'success')
            else:
                flash('Transaction not found or unauthorized.', 'danger')

        elif action == 'update':
            # Update the category
            new_category = request.form.get('category')
            tx = Transaction.query.get(transaction_id)
            if tx and tx.user_id == current_user.id:
                tx.category = new_category
                db.session.commit()
                flash('Transaction updated successfully.', 'success')
            else:
                flash('Transaction not found or unauthorized.', 'danger')

        return redirect(url_for('main.transactions'))

    # Fetch all transactions for the current user
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    return render_template('transactions.html', transactions=transactions, form=TransactionForm())


@main.route('/submission', methods=['GET'])
@login_required
def submission():
    count    = request.args.get('count', type=int)
    if count is not None:
        # Only CSV path
        return render_template('submission.html', count=count)

    # Otherwise, manual path passes amount/category/date/tx_type
    amount   = request.args.get('amount')
    category = request.args.get('category')
    date      = request.args.get('date')
    tx_type  = request.args.get('tx_type')
    return render_template(
        'submission.html',
        count    = None,
        amount   = amount,
        category = category,
        date     = date,
        tx_type  = tx_type
    )


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



#   +++++++ API endpoints +++++++
#   grouped by category
@main.route('/api/transaction')
@login_required
def api_transactions():
    # fetch all of this user’s transactions, ordered by date
    rows = (Transaction.query
            .filter_by(user_id=current_user.id)
            .order_by(Transaction.date)
            .all())

    # group by category
    grouped = defaultdict(list)
    for t in rows:
        grouped[t.category].append({
            'date':   t.date.isoformat(),
            'amount': float(t.amount),     # convert Decimal to float for JSON
            'type':   t.type.value,              # expense | income | transfer
            'description': t.description,   
            **({'direction': t.transfer_direction} if t.transfer_direction else {})
        })

    data = []
    for category, items in grouped.items():
        # only keep the last 100 entries per category
        items = items[-100:]
        data.append({
            'category': category,
            'history':  items
        })

    return jsonify(data)



@main.route('/api/update_transaction', methods=['POST'])
@login_required
def api_update_transaction():
    data = request.get_json(silent=True) or {}
    transaction_id = data.get('transaction_id')
    new_category = data.get('category')

    if not transaction_id or not new_category:
        return jsonify({'error': 'Invalid data'}), 400

    tx = Transaction.query.get(transaction_id)
    if not tx or tx.user_id != current_user.id:
        return jsonify({'error': 'Transaction not found or unauthorized'}), 404

    tx.category = new_category
    db.session.commit()
    return jsonify({'success': True, 'category': new_category}), 200



@main.route("/api/user_search")
@login_required
def api_user_search():
    q = request.args.get("q", "").strip()
    query = User.query.filter(User.id != current_user.id)
    if q:
        query = query.filter(User.username.ilike(f"%{q}%"))
    matches = query.order_by(User.username).limit(10).all()

    # pre-fetch  friend IDs into a set
    my_friend_ids = {u.id for u in current_user.friends}

    payload = []
    for u in matches:
        payload.append({
            "id":         u.id,
            "username":   u.username,
            "is_friend":  u.id in my_friend_ids
        })
    return jsonify(payload)



#   +++++++ helper functions +++++++
VENDOR_MAP = {
    "woolworth":   "Groceries",
    "coles":       "Groceries",
    "uber":        "Transport",
    "transperth":   "Transport",
    "shell":       "Fuel",
    "netflix":     "Entertainment",
    "balthazar":   "Restaurant",
    "interest":    "Interest",
    "savings":     "Savings",
}


def categorize_by_vendor(desc: str):
    text = desc.lower()
    for vendor, cat in VENDOR_MAP.items():

        if re.search(rf'\b{re.escape(vendor)}\b', text):
            return cat
    return None


#  get sum of a category in a given year+month
def sum_category(cat_name, year, month, tx_type='expense'):
    q = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.user_id == current_user.id,
        extract('year', Transaction.date) == year,
        extract('month', Transaction.date) == month,
    )
    if cat_name:
        q = q.filter(Transaction.category == cat_name)
    if tx_type:
        q = q.filter(Transaction.type == tx_type)
    return q.scalar()




