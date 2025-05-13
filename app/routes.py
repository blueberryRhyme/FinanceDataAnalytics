import csv
import re
import numpy as np
from collections import defaultdict
from math import ceil
from io import TextIOWrapper
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from .models import User, UserSettings, Transaction, TransactionType, Bill, BillMember,BillTransaction, TransactionFriend
from app.forms import TransactionForm, RegistrationForm, LoginForm, LogoutForm
from datetime import datetime,date, timedelta
from dateutil.relativedelta import relativedelta
from rapidfuzz import fuzz
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func, extract


main = Blueprint('main', __name__)



# ++++++++++++++++++++++ home and dashboard +++++++++++++++++++++
@main.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.profile'))
    return render_template('home6.html')


@main.route('/dashboard')
@login_required
def dashboard():
    data = gather_dashboard_data(current_user)
    return render_template('dashboard.html', **data)

@main.route('/shared_dashboard/<int:user_id>')
@login_required
def shared_dashboard(user_id):
    other = User.query.get_or_404(user_id)

    # only allow if `other` friended you
    if other not in current_user.friended_by:
        abort(403)

    # reuse your dashboard logic
    data = gather_dashboard_data(other)
    # pass in `shared_user` so the template can say “Viewing X’s dashboard”
    return render_template(
    'dashboard.html',
    **data,
    shared_user      = other.username,   # for the H1
    view_user_id     = other.id          # for JS
)

# ++++++++++++++++++++++ END home and dashboard +++++++++++++++++++++



# ++++++++++++++++++++++ user management +++++++++++++++++++++
@main.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # hash the password
        pw_hash = generate_password_hash(form.password.data)
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
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.profile'))
        flash('Login failed. Check your email and password.', 'danger')

    return render_template('login.html', form=form)


@main.route('/profile')
@login_required
def profile():
    logout_form = LogoutForm()
    return render_template('profile.html',logout_form=logout_form)

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


@main.route("/api/add_friend", methods=["POST"])
@login_required
def api_add_friend():
    data = request.get_json(silent=True) or {}
    friend_id = data.get("friend_id")

    # quick validations
    if not isinstance(friend_id, int) or friend_id == current_user.id:
        abort(400, "Invalid friend_id")

    friend = User.query.get_or_404(friend_id)

    if friend in current_user.friends:
        return jsonify({"status": "already_friends"}), 200

    current_user.friends.append(friend)
    db.session.commit()
    return jsonify({"status": "added"}), 201


@main.route("/api/remove_friend", methods=["POST"])
@login_required
def api_remove_friend():
    data = request.get_json(silent=True) or {}
    friend_id = data.get("friend_id")

    if not isinstance(friend_id, int) or friend_id == current_user.id:
        abort(400, "Invalid friend_id")

    friend = User.query.get_or_404(friend_id)

    if friend not in current_user.friends:
        return jsonify({"status": "not_friends"}), 200

    current_user.friends.remove(friend)
    db.session.commit()
    return jsonify({"status": "removed"}), 200


@main.route("/api/friends")
@login_required
def api_friends():
    payload = [
        {"id": f.id, "username": f.username}
        for f in sorted(current_user.friends, key=lambda u: u.username.lower())
    ]
    return jsonify(payload)

@main.route('/api/shared_users')
@login_required
def api_shared_users():
    shared = list(current_user.friended_by)  
    shared.sort(key=lambda u: u.username)
    return jsonify([{"id": u.id, "username": u.username} for u in shared])



@main.route('/api/update_settings', methods=['POST'])
@login_required
def api_update_settings():
    data = request.get_json(silent=True)
    if not data:
        abort(400, 'Invalid payload')

    currency = data.get('currency', '').strip()
    budget   = data.get('budget')
    if not currency or not isinstance(budget, (int, float)):
        abort(400, 'currency and budget are required')

    if current_user.settings is None:
        current_user.settings = UserSettings(user_id=current_user.id)
        db.session.add(current_user.settings)

    current_user.settings.currency       = currency
    current_user.settings.monthly_budget = budget
    db.session.commit()

    return jsonify(
        currency=current_user.settings.currency,
        budget=   float(current_user.settings.monthly_budget)
    ), 200


# ++++++++++++++++++++++ END user management +++++++++++++++++++++




# ++++++++++++++++++++++ transaction management +++++++++++++++++++++
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
                    cat     = 'income'
                else:
                    tx_type = 'expense'
                    amt     = abs(amt)
                    cat     = categorize_by_vendor(desc) or 'uncategorized'

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

@main.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    """List user transactions with inline edit/delete (50 per page)."""
    PER_PAGE = 50
    page = request.args.get('page', 1, type=int)

    # ── Handle edit / delete via standard form post ─────────────
    if request.method == 'POST':
        action = request.form.get('action')
        tx_id  = request.form.get('transaction_id', type=int)
        if not tx_id:
            abort(400, description="Missing transaction_id")

        tx = Transaction.query.get_or_404(tx_id)
        if tx.user_id != current_user.id:
            abort(403)

        if action == 'delete':
            db.session.delete(tx)
            db.session.commit()
            flash('Transaction deleted.', 'success')

        elif action == 'update':
            new_cat = request.form.get('category', '').strip()
            if not new_cat:
                flash('Category cannot be empty.', 'warning')
            else:
                tx.category = new_cat
                db.session.commit()
                flash('Category updated.', 'success')
        else:
            flash('Unsupported action.', 'danger')

        # stay on the same page after the post/redirect/get cycle
        return redirect(url_for('main.history', page=page))

    pagination = (Transaction.query
                  .filter_by(user_id=current_user.id)
                  .order_by(Transaction.date.desc())
                  .paginate(page=page, per_page=PER_PAGE, error_out=False))

    return render_template(
        'history.html',
        transactions=pagination.items,
        TransactionType=TransactionType,
        pagination=pagination,     
        form=TransactionForm()
    )

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

#   grouped transaction by category
@main.route('/api/transaction')
@login_required
def api_transactions():
    uid = current_user.id

    # if the front-end passed ?view_user_id=XYZ, and XYZ != current_user.id,
    # check that XYZ has friended you, then switch to that ID
    view_id = request.args.get('view_user_id', type=int)
    if view_id and view_id != current_user.id:
        other = User.query.get_or_404(view_id)
        if other not in current_user.friended_by:
            abort(403)
        uid = other.id

    rows = (Transaction.query
            .filter_by(user_id=uid)
            .order_by(Transaction.date)
            .all())

    # group by category
    grouped = defaultdict(list)
    for t in rows:
        key = (t.category or '').strip().lower()
        grouped[key].append({
            'id':         t.id,
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

#   ++++++++++++++++++++++ END transaction management +++++++++++++++++++++






#   ++++++++++++++++++++++ forecast ++++++++++++++++++++++++++++++

@main.route("/forecast")
@login_required
def forecast():
    return render_template("forecast.html")




@main.route("/api/forecast")
@login_required
def api_forecast():
    window = request.args.get("months", default=12, type=int)
    window = max(3, min(window, 36))            # clamp 3-36

    hist_months  = month_starts(-(window-1), window)
    future_lbls  = [d.strftime("%b %Y") for d in month_starts(+1, 6)]

    # pull user's expense rows
    rows = (Transaction.query
            .filter(Transaction.user_id == current_user.id,
                    Transaction.type == TransactionType.expense)
            .order_by(Transaction.date)
            .all())

    # aggregate: category → {(yr,mo): total}
    cat_month_totals = defaultdict(lambda: defaultdict(float))
    for t in rows:
        ym = (t.date.year, t.date.month)
        key = t.category.strip().lower()
        cat_month_totals[key][ym] += float(t.amount)

    cat_forecasts = {}
    for cat, month_dict in cat_month_totals.items():        
        series = [month_dict.get((d.year, d.month), 0.0)    
                  for d in hist_months]
        cat_forecasts[cat] = linear_forecast(series,
                                             steps=6,
                                             window=window)

    overall = np.sum(list(cat_forecasts.values()), axis=0).round(2).tolist()

    return jsonify(months=future_lbls,
                   categories=cat_forecasts,
                   overall=overall)
@main.route("/api/forecast_simulate", methods=["POST"])
@login_required
def api_forecast_simulate():
    data   = request.get_json() or {}
    # robust parse for delta_amount
    raw    = data.get("delta_amount", 0)
    try:
        delta = float(raw) if str(raw).strip() else 0.0
    except ValueError:
        delta = 0.0

    cat    = data.get("category")  # None ⇒ overall
    base   = api_forecast().json
    series = base["categories"].get(cat, base["overall"]) if cat else base["overall"]

    adjusted = [round(v + delta, 2) for v in series]
    abs_delta = abs(delta)

    if delta == 0:
        advice = "No change — forecast unchanged."
    else:
        if delta > 0:
            verb = f"Spending ${abs_delta:.0f} more"
        else:  # delta < 0
            verb = f"Spending ${abs_delta:.0f} less"      # or “Cutting”

        prefix = (f"{verb} each month in '{cat}' "
                if cat else
                f"{verb} overall each month ")

        advice = prefix + f"would push your 6-month projection to ${adjusted[-1]:,.0f}."

        budget_dec = getattr(current_user.settings, "monthly_budget", None)
        budget = float(budget_dec) if budget_dec is not None else None

        if delta > 0 and budget and adjusted[-1] > 0.9 * budget:
            advice += " That’s close to your budget—consider trimming elsewhere."
        elif delta < 0:
            advice += " Good move—projection stays comfortably under budget."

    return jsonify(series=adjusted, advice=advice)

#   ++++++++++++++++++++++ END forecast ++++++++++++++++++++++++++++++


#   ++++++++++++++++++++++ bill splitting +++++++++++++++++++++
@main.route('/splitBill')
@login_required
def splitBill():                      
    """
    Renders the bill-splitting workspace.
    • `transactions` – last 200 transfers/in-flow/out-flow records
                       (enough for fuzzy matching)
    • `friends`      – current_user.friends for the dropdown
    """
    recent_tx = (Transaction.query
                 .filter(Transaction.user_id == current_user.id,
                         Transaction.type.in_([
                         TransactionType.transfer,
                         TransactionType.expense,
                         TransactionType.income
                        ]))
                 .order_by(Transaction.date.desc())
                 .limit(200)
                 .all())

    friends = sorted(current_user.friends, key=lambda u: u.username.lower())

    return render_template(
        'splitBill.html',
        transactions=recent_tx,
        friends=friends,
    )


@main.route('/bills')
@login_required
def bills_overview():
    # bills you created OR you are a member of
    q = (Bill.query
         .filter(
            db.or_(
              Bill.created_by == current_user.id,
              Bill.members.any(BillMember.user_id == current_user.id)
            ))
         .order_by(Bill.date.desc()))
    print(q.all())
    return render_template('bills.html', bills=q.all())


@main.route('/bill/<int:bill_id>')
@login_required
def bill_detail(bill_id):
    bill = Bill.query.get_or_404(bill_id)

    # security: must be creator or member
    member_ids = {bm.user_id for bm in bill.members}
    if current_user.id not in member_ids and bill.created_by != current_user.id:
        abort(403)

    #  get all transactions that are linked to the bill
    cand_q = (Transaction.query
                    .join(TransactionFriend, Transaction.id == TransactionFriend.transaction_id)
                    .filter(TransactionFriend.friend_id.in_(member_ids))
             )

    # only keep those with a positive remaining amount
    suggested = [t for t in cand_q
                     if t.remaining > 0]

    return render_template(
        'bill_detail.html',
        bill=bill,
        members=bill.members,
        suggested=suggested
    )

@main.route("/api/bill/suggest_friends/<int:tx_id>")
@login_required
def api_bill_suggest_friends(tx_id):

    tx = Transaction.query.get_or_404(tx_id)
    if tx.user_id != current_user.id:
        abort(403)

    results = similar_transfers(tx, threshold=85)
    payload = [{
        "id": t.id,
        "date": t.date.isoformat(),
        "desc": t.description,
        "amount": float(t.amount),
        "score": score
    } for t, score in results]

    return jsonify(payload)


@main.route("/api/bill/associate", methods=["POST"])
@login_required
def api_bill_associate_friend():
    """
    Body: { transaction_id: int, friend_id: int, confidence: float? }
    Links a single transaction to a friend.
    """
    data = request.get_json(silent=True) or {}
    tx_id     = data.get("transaction_id")
    friend_id = data.get("friend_id")
    conf      = float(data.get("confidence", 1.0))

    tx   = Transaction.query.get_or_404(tx_id)

    existing = TransactionFriend.query.filter_by(transaction_id=tx_id).first()
    if existing:
        # remind who it’s linked to
        other = User.query.get(existing.friend_id)
        return jsonify({"error": f"Already tagged to {other.username}"}), 400

    fr   = User.query.get_or_404(friend_id)

    if tx.user_id != current_user.id or fr not in current_user.friends:
        abort(403)

    link = TransactionFriend(transaction_id=tx.id,
                             friend_id=fr.id,
                             confidence=conf)
    db.session.merge(link)          
    db.session.commit()
    return "", 204

from decimal import Decimal, ROUND_HALF_UP

@main.route("/api/bill/create", methods=["POST"])
@login_required
def api_bill_create():
    data      = request.get_json(force=True)
    tx_ids    = data.get("transaction_ids", [])
    friend_ids= data.get("member_ids", [])
    details   = data.get("details")

    txs = Transaction.query.filter(Transaction.id.in_(tx_ids)).all()
    if len(txs) != len(tx_ids) or any(tx.user_id != current_user.id for tx in txs):
        abort(403, "Invalid or unauthorized transactions")

    friends = User.query.filter(User.id.in_(friend_ids)).all()
    if {u.id for u in friends} != set(friend_ids):
        abort(403, "Some member_ids invalid")
    for f in friends:
        if f not in current_user.friends:
            abort(403, f"{f.username} is not your friend")

    #  Build deduped member list (always include creator - current user)
    members = [current_user] + friends
    unique  = {}
    for u in members:
        unique[u.id] = u
    members = list(unique.values())

    total    = sum(Decimal(str(tx.amount)) for tx in txs)
    per_head = (total / Decimal(len(members))).quantize(
                  Decimal("0.01"), rounding=ROUND_HALF_UP
               )

    if not details and txs:
        details = txs[0].description
    desc = (details or "").strip()[:240]

    bill = Bill(
        created_by  = current_user.id,
        description = desc,
        total       = total
    )
    db.session.add(bill)
    db.session.flush()  

    BillMember.query.filter_by(bill_id=bill.id).delete()

    for u in members:
        #  if the user is the creator, assume they have paid their share( since the transaction belongs to the creator)
        if u.id == current_user.id:
            paidAmt = per_head
        else:
            paidAmt = Decimal("0.00")
        bm = BillMember(
            bill_id = bill.id,
            user_id = u.id,
            share   = per_head,
            paid    = paidAmt,
            settled = False
        )
        db.session.add(bm)

    db.session.commit()

    return jsonify({"bill_id": bill.id}), 201

@main.route("/api/bill/<int:bill_id>")
@login_required
def api_bill_get(bill_id):

    bill = Bill.query.get_or_404(bill_id)
    # visibility: creator or member
    member_ids = {bm.user_id for bm in bill.members}
    print(f"member_ids {member_ids}")
    if current_user.id not in member_ids and bill.created_by != current_user.id:
        abort(403)

    return jsonify({
        "id":          bill.id,
        "description": bill.description,
        "date":        bill.date.isoformat(),
        "total":       float(bill.total),
        "members": [{
            "user_id": bm.user_id,
            "username": bm.user.username,
            "share":  float(bm.share),
            "paid":   float(bm.paid),
            "settled": bm.settled
        } for bm in bill.members]
    })

@main.route('/bill/<int:bill_id>/delete', methods=['POST'])
@login_required
def bill_delete(bill_id):
    bill = Bill.query.get_or_404(bill_id)
    # only creator may delete
    if bill.created_by != current_user.id:
        abort(403)
    db.session.delete(bill)
    db.session.commit()
    flash('Bill deleted.', 'success')
    return redirect(url_for('main.bills_overview'))


@main.route('/api/bill/<int:bill_id>/apply_transaction', methods=['POST'])
@login_required
def api_apply_transaction(bill_id):
    data = request.get_json(force=True)
    tx_id = data.get('transaction_id')
    amt   = Decimal(str(data.get('amount_applied', 0)))

    bill = Bill.query.get_or_404(bill_id)
    if bill.created_by != current_user.id:
        abort(403)

    # make sure the tx was suggested & not already used:
    used = {bt.transaction_id for bt in bill.transactions}
    if tx_id in used:
        abort(400, "Already applied")
    # you could also re-run fuzzy logic / friend check here if you like

    # create the BillTransaction
    bt = BillTransaction(
      bill_id=bill.id,
      transaction_id=tx_id,
      amount_applied=amt
    )
    db.session.add(bt)

    tf = TransactionFriend.query.filter_by(transaction_id=tx_id).first()
    if tf:
        bm = BillMember.query.filter_by(bill_id=bill.id, user_id=tf.friend_id).one()
        bm.paid += amt

    db.session.commit()
    return jsonify({
        "user_id":         bm.user_id,
        "new_outstanding": float(bm.share - bm.paid),
        "new_paid":      float(bm.paid),
        "transaction": {
            "id":            tx_id,
            "date":          bt.transaction.date.isoformat(),
            "description":   bt.transaction.description,
            "amount_applied": float(amt)
        }
    }), 200

#   ++++++++++++++++++++++ END bill splitting +++++++++++++++++++++




#   ++++++++++++++++++++ helper functions +++++++++++++++++++++
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
def sum_category(cat_name, year, month, tx_type='expense', user=None):
    
    uid = user.id if user is not None else current_user.id
    q = db.session.query(
            func.coalesce(func.sum(Transaction.amount), 0)
        ).filter(
            Transaction.user_id == uid,
            extract('year', Transaction.date) == year,
            extract('month', Transaction.date) == month,
        )
    if cat_name:
        q = q.filter(Transaction.category == cat_name)
    if tx_type:
        q = q.filter(Transaction.type == tx_type)
    return q.scalar()

def gather_dashboard_data(user):
    today = date.today()
    ym_this = (today.year, today.month)
    last_month = (today.replace(day=1) - timedelta(days=1))
    ym_last = (last_month.year, last_month.month)

    total_exp_this = sum_category(None, *ym_this, tx_type="expense", user=user)
    total_exp_last = sum_category(None, *ym_last, tx_type="expense", user=user)
    exp_pct_change = ((total_exp_this - total_exp_last) / total_exp_last * 100) if total_exp_last else 0

    savings_this = sum_category('savings', *ym_this, tx_type='income', user=user)
    savings_last = sum_category('savings', *ym_last, tx_type='income', user=user)
    sav_pct_change = ((savings_this - savings_last) / savings_last * 100) if savings_last else 0

    # ensure settings exist
    if user.settings is None:
        user.settings = UserSettings(user_id=user.id)
        db.session.add(user.settings)
        db.session.commit()

    budget    = user.settings.monthly_budget
    remaining = budget - total_exp_this
    rem_pct   = (remaining / budget * 100) if budget else 0

    return {
        'total_expenses': round(total_exp_this, 2),
        'exp_pct_change': round(exp_pct_change, 1),
        'savings':        round(savings_this, 2),
        'sav_pct_change': round(sav_pct_change, 1),
        'budget':         round(budget, 2),
        'rem_pct':        round(rem_pct, 1),
    }

#    weighted linear regression: newer months weigh more
def linear_forecast(history, steps=6, window=12):
    tail = history[-window:]
    if len(tail) < 2:
        return [tail[-1] if tail else 0.0] * steps
    x = np.arange(len(tail))
    w = np.linspace(0.1, 1.0, len(tail))
    m, b = np.polyfit(x, tail, 1, w=w)
    future_x = np.arange(len(tail), len(tail)+steps)
    return list((m * future_x + b).round(2))

def month_starts(offset: int, count: int):
    """Return `count` first-of-month date objects starting `offset` months from now."""
    start = date.today().replace(day=1) + relativedelta(months=offset)
    step  = 1 if count > 0 else -1
    return [(start + relativedelta(months=i)).replace(day=1)
            for i in range(0, count, step)]


def similar_transfers(base_tx, threshold: int = 80, limit: int = 20):
    """
    Return [(Transaction, score), …] that look like `base_tx`
    (case-insensitive token-set fuzzy match on description).
    """
    q = (Transaction.query
                     .filter(Transaction.user_id == base_tx.user_id,
                             Transaction.id != base_tx.id)
                     .limit(500))                # early cap for perf

    matches = []
    base_desc = base_tx.description.lower()
    for cand in q:
        score = fuzz.token_set_ratio(base_desc, cand.description.lower())
        if score >= threshold:
            matches.append((cand, score))

    matches.sort(key=lambda t: -t[1])
    return matches[:limit]

def create_equal_bill(creator, transactions, members, details=None):
    from decimal import Decimal, ROUND_HALF_UP

    # sum up the amounts precisely
    total = sum(Decimal(str(t.amount)) for t in transactions)
    print(f"Total: {total}")
    per_head = (total / Decimal(len(members))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # if the front-end sent us a details string, use it
    description = details or "; ".join(
        {t.description for t in transactions}
    )[:240]

    bill = Bill(
        created_by  = creator.id,
        description = description,
        total       = total
    )
    bill.members.extend(
        BillMember(user_id=m.id, share=per_head, paid=Decimal("0.00"))
        for m in members
    )

    # Optionally: link each selected transaction to the bill's creator as a 'friend'
    # by creating TransactionFriend entries here if that's your model.

    db.session.add(bill)
    return bill