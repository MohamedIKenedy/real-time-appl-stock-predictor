from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, IntegerField, FileField, TextAreaField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError, regexp
from application.models import User
from application.nasdaq import nasdaq

class RegisterForm(FlaskForm):
    def validate_username(self, username_to_check):
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different username')
    
    def validate_email_address(self, email_address_to_check):
        user = User.query.filter_by(email_address=email_address_to_check.data).first()
        if user:
            raise ValidationError('Email address already exists! Please try a different email address')
    
    username = StringField(label = 'Username:', validators= [Length(min=2, max=30), DataRequired()])
    email_address = StringField(label = 'Email Address:', validators=[Email(), DataRequired()])
    password1 = PasswordField(label = 'Password:', validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label = 'Confirm Password:', validators=[EqualTo('password1'), DataRequired()])
    submit = SubmitField(label='Create Account')

class LoginForm(FlaskForm):
    username = StringField(label = 'User Name:', validators= [DataRequired()])
    password = PasswordField(label = 'Password:', validators= [Length(min=6), DataRequired()])
    submit = SubmitField(label = 'Sign in')

class StockForm(FlaskForm):
    company =  SelectField('Company Symbol', choices=nasdaq)
    num_days = IntegerField(label ='Amount of days to scrap', default=100)
    order = SelectField('Date Order of the data', choices=[('ASC','ASCENDANT'), ('DESC','DESCENDANT')])
    extension = SelectField('Download as', choices=[('CSV','CSV file'), ('XLSX','EXCEL file')])

class UploadForm(FlaskForm):
    file = FileField(label="Choose a File", validators= [DataRequired()])
    num_days = IntegerField(label ='Amount of days to forecast', default=30, validators= [DataRequired()])
    extension = SelectField('Download as', choices=[('CSV','CSV file'), ('XLSX','EXCEL file')])


class PredictForm(FlaskForm):
    window_size = IntegerField(label ='How much days in the past to take into account when predicting the future ?', default=90, validators= [DataRequired()])
    target_size = IntegerField(label ='Number of days ahead of today to forecast', default=7, validators= [DataRequired()])
    epochs = IntegerField(label ='Number of Training Iterations', default=10, validators= [DataRequired()])
    submit = SubmitField(label = 'Predict')