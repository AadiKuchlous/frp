# -*- coding: utf-8 -*-

import os
import sets
from flask import (render_template,
                   g,
                   url_for,
                   redirect,
                   session,
                   flash,
                   views,
                   request,
                   jsonify)
from flask.ext.oauth import OAuth
from werkzeug import secure_filename
from flask_login import login_user

from .. import app
from ..models import (Campaign, ORG_STATUS_CHOICES)
from ..forms import (BeneficiarySignupForm,
                     ProfileForm,
                     CategoryForm,
                     CampaignForm)
from ..service import signup as signup_service
from ..service import user as user_service
from flask_user import current_user, login_required, roles_required
from ..helpers import allowed_file

# Facebook requirements
oauth = OAuth()

facebook = oauth.remote_app(
    'facebook',
    request_token_url=None,
    base_url='https://graph.facebook.com/',
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=app.config.get('FACEBOOK_CONSUMER_KEY'),
    consumer_secret=app.config.get('FACEBOOK_CONSUMER_SECRET'),
    request_token_params={'scope': 'email'})

@facebook.tokengetter
def get_facebook_token():
    return session.get('facebook_token')

def pop_login_session():
    session.pop('logged_in', None)
    session.pop('facebook_token', None)
    session.pop('email', None)

@app.route('/campaign/success')
@login_required
def campaign_success():
    return render_template('campaignSuccess.html')

@app.route('/signup/beneficiary', methods=['GET', 'POST'])
@login_required
def signup_as_beneficiary():
    if request.method == 'GET':
        form = BeneficiarySignupForm()
        if (current_user.organization_created):
            form.set_data(current_user.organization_created[0])
        return render_template('beneficiary_form.html', form=form)

    elif request.method == 'POST':
        form = BeneficiarySignupForm(request.form)
        if form.validate():
            image = request.files['imageUpload']
            filename = secure_filename(image.filename)
            if filename and allowed_file(filename):
                full_save_path = os.path.join(app.config['UPLOAD_DIRECTORY'], 'tmp', filename)
                image.save(full_save_path)

            result = signup_service.create_beneficiary(form, filename)
            if not result['error']:
                return redirect(url_for('campaign_success'))
            else:
                flash('Oops something went wrong, please try again')

        print form.errors
        return render_template('beneficiary_form.html', form=form)

# Login views
@app.route('/login/facebook', methods=['GET', 'POST'])
def login_via_facebook():
    if request.args.get('next'):
        return facebook.authorize(
            callback=url_for('facebook_authorized',
                         next=request.args.get('next'),
                         _external=True))
    else:
        return facebook.authorize(
            callback=url_for('facebook_authorized',
                         _external=True))


@app.route("/login/facebook_authorized")
@facebook.authorized_handler
def facebook_authorized(resp):
    next_url = request.args.get('next') or url_for('index')
    if resp is None or 'access_token' not in resp:
        return redirect(next_url)

    session['logged_in'] = True
    session['facebook_token'] = (resp['access_token'], '')
    data = facebook.get('me')

    user = signup_service.create_donor_from_facebook(data.data)
    login_user(user=user)
    return redirect(next_url)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')


class EditProfile(views.MethodView):
    @login_required
    def get(self):
        form = ProfileForm()
        # We don't need password, email field
        form.set_data(current_user)
        return render_template('edit_profile.html', form=form)

    @login_required
    def post(self):
        form = ProfileForm(request.form)
        if form.validate():
            user_service.update_profile(form)
            return redirect(url_for('profile'))
        return render_template('edit_profile.html', form=form)


app.add_url_rule('/profile/edit',
                 view_func=EditProfile.as_view('edit_profile'))


@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/discover", methods=['GET'])
def discover():
    campaigns_data = Campaign.all_campaigns_data()
    return render_template('discover.html', campaigns_data=campaigns_data)

@app.route("/start", methods=['GET', 'POST'])
@login_required
def start():
    if request.method == 'GET':
        form = BeneficiarySignupForm()
        if (current_user.organization_created):
            form.set_data(current_user.organization_created[0])
        return render_template('start.html', form=form)
    elif request.method == 'POST':
        form = BeneficiarySignupForm(request.form)
        if form.validate():
            image = request.files['imageUpload']
            filename = secure_filename(image.filename)
            if filename and allowed_file(filename):
                full_save_path = os.path.join(app.config['UPLOAD_DIRECTORY'], 'tmp', filename)
                image.save(full_save_path)

            result = signup_service.create_beneficiary(form, filename)
            if not result['error']:
                return redirect(url_for('campaign_success'))
            else:
                flash('Oops something went wrong, please try again')

        print form.errors
        return render_template('start.html', form=form)


@app.route("/profile/donor_dashboard")
@login_required
def donor_dashboard():
    return render_template('donorDashboard.html')

@app.route("/profile/beneficiary_dashboard")
@login_required
def beneficiary_dashboard():
    campaigns = current_user.campaigns
    active_campaigns=0
    closed_campaigns=0
    active_donors = []
    closed_donors = []
    total_active_amt=0
    total_closed_amt=0

    for campaign in campaigns:
        if campaign.is_active():
            active_campaigns+=1
            active_donors+=campaign.donor_list()
            total_active_amt+= sum(campaign.donations)

        else:
            closed_campaigns+=1
            closed_donors+=campaign.donor_list()
            total_closed_amt+= sum(campaign.donations)

    n_active_donors = len(sets.Set(active_donors))
    n_closed_donors = len(sets.Set(closed_donors))
    num_books_recvd_active = int(total_active_amt/50)
    num_books_recvd_closed = int(total_closed_amt/50)
    return render_template('beneficiaryDashboard.html',campaigns=campaigns,
            active_campaigns=active_campaigns,
            closed_campaigns=closed_campaigns,
            total_active_amt=total_active_amt,
            total_closed_amt=total_closed_amt,
            n_active_donors=n_active_donors,
            n_closed_donors=n_closed_donors,
            num_books_recvd_active=num_books_recvd_active,
            num_books_recvd_closed=num_books_recvd_closed
            )


@app.context_processor
def convertStatusTypeToString():
    def statusString(status):
        return ORG_STATUS_CHOICES[status]
    return dict(statusString=statusString)

@app.route("/campaign/<id>", methods=['GET'])
def campaignPage(id):
    campaign = Campaign.query.filter_by(id=id).first()
    return render_template('campaign.html', campaign=campaign)
