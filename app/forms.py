
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, DateField, SubmitField, PasswordField,BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Email, EqualTo, ValidationError
from app.models import User 


class LogoutForm(FlaskForm):
    submit = SubmitField('Log out')

class ExpenseForm(FlaskForm):
    amount = DecimalField(
        'Amount',
        validators=[DataRequired(), NumberRange(min=0.01)],
        places=2,
    )
    category = SelectField(
        'Category',
        choices=[
            ('', '— choose one —'),
            ('food', 'Food'),
            ('shopping', 'Shopping'),
            ('health', 'Health'),
            ('other', 'Other'),
        ],
        validators=[DataRequired()]
    )
    other_category = StringField(
        'Please specify',
        validators=[Optional()]
    )
    date = DateField(
        'Date',
        format='%Y-%m-%d',
        validators=[DataRequired()]
    )
    submit = SubmitField('Submit')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email    = StringField('Email',    validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm  = PasswordField('Confirm Password',
                             validators=[DataRequired(), EqualTo('password')])
    submit   = SubmitField('Register')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('That username is taken.')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('That email is already registered.')
        
class LoginForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[DataRequired(), Email()]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
    )
    remember = BooleanField(
        'Remember Me'
    )
    submit = SubmitField(
        'Log In'
    )