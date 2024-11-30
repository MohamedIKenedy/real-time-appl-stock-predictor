import pandas as pd
from application import app, db
from flask import render_template, url_for, redirect, flash,  request
from application.models import User
from application.forms import RegisterForm, LoginForm, PredictForm
from flask_login import login_user, logout_user
import plotly.express as px
from application.utils import main

#global variables that I needed to transfer from route to route
loaded_data=pd.DataFrame()
forecast=pd.DataFrame()
company_sym = ""
fig2 = 0


@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')



@app.route('/register', methods=['GET','POST'])
def register_page():
    db.create_all()
    form = RegisterForm()
    print("1"*100)
    if form.validate_on_submit():
        print("1"*100)
        user_to_create = User(username=form.username.data, email_address=form.email_address.data, password=form.password1.data)
        print("2"*100)
        db.session.add(user_to_create)
        print("3"*100)
        db.session.commit()
        return redirect(url_for('home_page'))
    if form.errors != {}:
        for err_msg in form.errors.values():
            flash(f'There was an error with creating a user: {err_msg}', category='danger')   
    return render_template('register.html', form=form)



@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard_page():
    return render_template('dashboard.html')


@app.route('/login', methods = ['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        print()
        attempted_user = User.query.filter_by(username=form.username.data).first()
        boolean_value=True
        try:
            boolean_value = attempted_user.check_password_correction(attempted_password=form.password.data)
        except ValueError:
            boolean_value = False
        except AttributeError:
            attempted_user = False
        else:
            pass
        if attempted_user and boolean_value:
            login_user(attempted_user)
            flash(f"Success! You are logged in as: {attempted_user.username}", category="success")
            return redirect(url_for("predict_page"))
        else:
            flash('Username and password are not matching! Please try again', category="danger")
    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash(f"You have been logged out!", category="info")
    return redirect(url_for('login_page'))


@app.route('/predict', methods=['POST', "GET"])
def predict_page():
    form = PredictForm(request.form)
    print(form.validate_on_submit())
    if request.method == "POST":
        window_size = form.window_size
        target_size = form.target_size
        main(window_size=window_size, target_size=target_size)
        return redirect(url_for('dashboard_page'))
        
    return render_template('predict.html', form=form)

# @app.route('/visulize_scrapped_data', methods=['GET', 'POST'])
# def vsd_page():
#     if request.method=="GET":
#         global loaded_data
#         company_symbol = loaded_data.loc[0,"Company Symbol"]
#         file = os.listdir('application/downloads')[0]
#         file_path = os.path.join('application/downloads',file)
#         fig1 = plot_raw_data(file_path=file_path,company_symbol=company_symbol)
#         graph1JSON = json.dumps(fig1 ,cls = plotly.utils.PlotlyJSONEncoder)
#         return render_template('df.html', tables=[loaded_data.to_html(classes=['table table-striped table-hover table-responsive'])], titles=loaded_data.columns.values, company_symbol=company_symbol,graph1JSON=graph1JSON)
#     elif request.method=="POST":
#         return redirect(url_for("download_file"))


# @app.route('/visulize_predictions', methods=['GET', 'POST'])
# def vp_page():
#     if request.method=='GET':
#         global forecast, company_sym, fig2
#         graph2JSON = json.dumps(fig2 ,cls = plotly.utils.PlotlyJSONEncoder)
#         return render_template('vp.html', tables=[ forecast.to_html( classes=[ 'table table-striped table-hover table-responsive' ] ) ], titles=forecast.columns.values, company_symbol=company_sym, graph2JSON=graph2JSON)
#     elif request.method == 'POST':
#         return redirect(url_for('download_file'))


# @app.route('/download')
# def download_file():
#     file=""
#     if os.path.exists("application/downloads/download.xlsx") and os.path.isfile('application/downloads/download.xlsx'):
#         file ='download.xlsx'
#     elif os.path.exists('application/downloads/download.csv') and os.path.isfile('application/downloads/download.csv'):
#         file = 'download.csv'
#     elif os.path.exists('application/downloads/forecast.csv') and os.path.isfile('application/downloads/forecast.csv'):
#         file = 'forecast.csv'
#     elif os.path.exists("application/downloads/forecast.xlsx") and os.path.isfile('application/downloads/forecast.xlsx'):
#         file = 'forecast.xlsx'       
#     path_file = os.path.join(r"downloads",file)
#     return send_file(path_file, as_attachment=True)
