
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import DecimalField, SelectField, StringField, DateField, SubmitField, PasswordField,BooleanField
from wtforms.validators import DataRequired, Optional, NumberRange, Email, EqualTo, ValidationError
from app.models import User 


class LogoutForm(FlaskForm):
    submit = SubmitField('Log out')


class TransactionForm(FlaskForm):
    type = SelectField(
        'Type',
        choices=[
            ('expense',  'Expense'),
            ('income',   'Income'),
            ('transfer', 'Transfer'),
        ],
        validators=[DataRequired("Choose expense, income, or transfer.")]
    )

    transfer_direction = SelectField(
        'Transfer Direction',
        choices=[
            ('in',  'Incoming (into this account)'),
            ('out', 'Outgoing (from this account)'),
        ],
        validators=[Optional()]
    )

    amount = DecimalField(
        'Amount',
        places=2,
        validators=[Optional(), NumberRange(min=0.01, message="Must be ≥ $0.01")]
    )

    category = SelectField(
        'Category',
        choices=[
            ('',         '— choose one —'),
            ('food',     'Food'),
            ('shopping', 'Shopping'),
            ('health',   'Health'),
            ('salary',   'Salary'),
            ('savings',  'Savings'),
            ('refund',   'Refund'),
            ('other',    'Other'),
        ],
        validators=[Optional()]
    )
    other_category = StringField(
        'If “Other,” please specify',
        validators=[Optional()]
    )
    description = StringField(
        'Description',
        validators=[Optional()]
    )

    date = DateField(
        'Date',
        format='%Y-%m-%d',
        validators=[Optional()]
    )

    csv_file = FileField(
        'Or upload CSV of transactions',
        validators=[Optional(), FileAllowed(['csv'], 'CSV files only')]
    )

    submit = SubmitField('Submit')


    def validate(self, extra_validators=None):
        """Either CSV upload or manual fields.  
           If manual, enforce based on type + transfer_direction."""
        # pass the extra_validators through to the base implementation
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False

        # CSV path short-circuits all manual requirements
        if self.csv_file.data:
            return True

        errors = False

        # always require amount and date when not CSV
        if self.amount.data is None:
            self.amount.errors.append("Amount is required.")
            errors = True

        if self.date.data is None:
            self.date.errors.append("Date is required.")
            errors = True

        # for expense/income require category (+ other if needed)
        if self.type.data in ('expense', 'income'):
            if not self.category.data:
                self.category.errors.append("Category is required.")
                errors = True
            elif self.category.data == 'other' and not (self.other_category.data or '').strip():
                self.other_category.errors.append("Please specify the other category.")
                errors = True

        # for transfer require transfer_direction
        if self.type.data == 'transfer':
            if not self.transfer_direction.data:
                self.transfer_direction.errors.append("Please choose incoming or outgoing.")
                errors = True

        return not errors
    

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