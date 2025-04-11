import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


basedir = os.path.abspath(os.path.dirname(__file__))


#   flask application instance 
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


@app.route('/')
def test():
    return render_template('home.html')

#   inherit from UserMixin  provides default implementations for properties and methods like 'is_authenticated', 'get_id()', etc

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)





@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #   Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')  

        # Check if the user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))

        # Create new user and add to database
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful, please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login')
def login():
    return render_template('login.html')

if __name__ == '__main__':
    with app.app_context():
        #   create the database at runtime?
        db.create_all() 
    app.run(debug=True)