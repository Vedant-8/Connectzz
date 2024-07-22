from models import User
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FloatField, IntegerField, SelectField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('sponsor', 'Sponsor'), ('influencer', 'Influencer')], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')

class CampaignForm(FlaskForm):
    name = StringField('Campaign Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    budget = FloatField('Budget', validators=[DataRequired()])
    visibility = SelectField('Visibility', choices=[('public', 'Public'), ('private', 'Private')], validators=[DataRequired()])
    goals = TextAreaField('Goals', validators=[DataRequired()])
    submit = SubmitField('Create Campaign')

class AdRequestForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    payment_amount = FloatField('Payment Amount', validators=[DataRequired()])
    submit = SubmitField('Submit Ad Request')

