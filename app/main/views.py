"""Route President"""
from flask import Flask, render_template, url_for, redirect, flash, session, request, Blueprint
from .forms import LoginForm, RegistrationForm, ConfirmationForm
import os
import json
import requests
from requests.exceptions import ConnectionError

main = Blueprint('main', __name__)

# a few globals
host_url = """https://ghastly-vault-37613.herokuapp.com/"""
headers = {
        'content-type': "application/json",
        'cache-control': "no-cache"
        }

@main.route('/')
def start():
    """the home page"""
    return redirect(url_for('main.home'))

@main.route('/landing')
def home():
    """landing page render -> change of plan the landing page will display tables that display the last 2 advisories"""
    return render_template('landing_page.html')

@main.route('/admin', methods=['GET', 'POST'])
def admin():
    """display the admin's tips approval page"""
    #here we connect to the api using authentication data provided and then receive the response and parse it on to the template
    form = ConfirmationForm()
    headers = {}
    try:
        headers['x-access-token'] = session['token']
    except KeyError as error:
        return redirect(url_for('main.login'))
    pred_url = host_url + '''predictions/'''
    if form.validate_on_submit():
        # there is some admin actions taking place
        q = request.args['pred_id']
        if q is None:
            # we have an error
            raise Exception('WE have an error or abort')
        else:
            # retrieve the form details and put
            data = {
                "comment": form.confirmation_text.data,
                "approved": True
            }
            print(data)
            pred_url += "{}".format(q)
            _response = requests.put(pred_url, data=json.dumps(data), headers=headers)
            print(_response.request.__repr__)
            if _response.status_code == 201:
                # success
                flash("Prediction approved")
                return redirect(url_for('main.admin'))
            else:
                flash("Prediction not approved")
                return redirect(url_for('main.admin'))

    response = requests.get(pred_url, headers=headers)
    if response.status_code == 200:
        # success
        preds = response.json()  # -> a dictionary with list of dictionaries
        predictions = preds['predictions']
        #separate the predictions into sections: all - >predictions, staged -> ?, and approved-> approved
        approved = []
        fields = {}
        fields['odds'] = 1
        fields['comment'] = ''
        for pred in predictions:
            if pred['approved']:
                approved.append(pred)
                fields['odds'] *= pred['odds']
                fields['comment'] += str(pred['comment'])
        return render_template('admin/admin.html', predictions=predictions, approved=approved, form=form, fields=fields)
    if response.status_code == 401:
        # unauthorized attempt
        flash("Session expired please login again", 'info')
        return redirect(url_for('main.logout'))
    else:
        return redirect(url_for('main.logout'))

@main.route('/invalidate/<pred_id>')
def invalidate(pred_id):
    """:param the predction id of the prediction instance to be invalidated"""
    pred_url = host_url + '''predictions/{}'''.format(pred_id)
    data = {
            "comment": "",
            "approved": False
        }
    _response = requests.put(pred_url, data=json.dumps(data), headers=headers)
    if _response.status_code == 201:
        # succesful modification return to admin
        flash("Prediction unapproved", "success")
        return redirect(url_for('main.admin'))
    else:
        flash("Prediction still valid", 'danger')
        return redirect(url_for('main.admin'))

@main.route("/users")
def user_predictions():
    """Renders the approved predictions"""
    try:
        token = session['token']
    except KeyError as error:
        return redirect('main.login')
    headers = {
        'x-access-token' : token
    }
    pred_url = host_url + '''predictions/'''
    response = requests.get(pred_url, headers=headers)
    if response.status_code == 200:
        # success
        preds = response.json()  # -> a dictionary with list of dictionaries
        predictions = preds['predictions']
        return render_template('user/user.html', predictions=predictions)
    elif response.status_code == 401:
        # unauthorized attempt
        info = response.json()
        flash("Session expired please login again,. {}".format(info), 'info')
        return redirect(url_for('main.login'))
    else:
        flash("Problem logging in, {}".format(response.status_code), 'danger')
        return redirect(url_for('main.login'))
    return render_template('user/user.html', predictions=predictions)

@main.route("/login", methods=['GET', 'POST'])
def login():
    """authenticate account with the api so as to receive the api token"""
    form = LoginForm()
    login_endpoint = host_url + """users/login"""
    if form.validate_on_submit():
        # form data processing
        data = {
          'user_name': form.user_name.data,
          'password': form.password.data
        }
        try:
            response = requests.post(login_endpoint, data=json.dumps(data), headers=headers)
        except ConnectionError:
            flash("Problem connecting to Ghastly API", 'warning')
            return "Try AGain LATer", 500
        if response.status_code == 200:
            # successfully verified-> retrieve the json data and get token
            response_data = response.json()
            token = response_data['token']
            admin = response_data['admin']
            # add the user to session and redirect to users/dashboard
            session['user_name'] = form.user_name.data
            session['token'] = token
            # should only redirect to users if the logged in person is not an administrator -> how do we know that a user is an admin
            if admin:
                return redirect(url_for('main.admin'))
            else:
                return redirect(url_for('main.user_predictions'))
        flash('{} {}'.format(response.status_code, response.content), 'danger')
    return render_template('user/login.html', form=form)


@main.route('/logout')
def logout():
    """disowns an in session token"""
    session.pop('user_name', None)
    session.pop('token', None)
    return redirect(url_for('main.home'))

@main.route("/register", methods=['GET', 'POST'])
def register():
    """Post new user data to the api"""
    # render a registration form and parse data to backend fields: name, user name, email, and password
    form = RegistrationForm()
    if form.validate_on_submit():
        # we have the validate go
        data = {
            'name' : form.name.data,
            'user_name' : form.user_name.data,
            'email' : form.email.data,
            'password' : form.password.data
        }
        # send the data to api await response and return template accordingly
        reg_endpoint = host_url + '''users/register'''
        try:
            response = requests.post(reg_endpoint, data=json.dumps(data), headers=headers)
        except ConnectionError:
            flash("Problem connecting to Ghastly API", 'warning')
            return "<h2>Try AGain LATer</h2>", 500
        if response.status_code == 201:
            flash("Account Created Succesfully", 'success')
            return redirect(url_for('main.login'))
        elif response.status_code == 400:
            flash("Bad request", 'danger')
            return render_template('user/register.html', form=form)
        else:
            # unknown problems : -> eradicate using tests..> u r such a rookie programmer
            flash("unknown problem {}".format(response.status_code), 'danger')
            return render_template('user/register.html', form=form)
      
    return render_template('user/register.html', form=form)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')