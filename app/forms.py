
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange

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
