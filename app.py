from flask import Flask, render_template, redirect, flash, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from models import db, User, Sponsor, Influencer, Campaign, CampaignInfluencer, AdRequest
from forms import LoginForm, RegisterForm, CampaignForm, AdRequestForm
from config import Config


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@app.route('/')
def home():
    return render_template('base.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'sponsor':
                return redirect(url_for('sponsor_dashboard'))
            elif user.role == 'influencer':
                return redirect(url_for('influencer_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        print('Account created successfully. Please log in.', 'success')
        if form.role.data == 'sponsor':
            new_sponsor = Sponsor(user_id=new_user.id, company_name='', industry='', budget=0.0)
            db.session.add(new_sponsor)
            db.session.commit()
        elif form.role.data == 'influencer':
            new_influencer = Influencer(user_id=new_user.id, name='', category='', niche='', reach=0)
            db.session.add(new_influencer)
            db.session.commit()
        return redirect(url_for('login')) 
    else:
        print(form.errors) 
    return render_template('register.html', form=form)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    users = User.query.all()
    sponsors = (
        db.session.query(Sponsor, User.username, Campaign.name)
        .join(User, Sponsor.user_id == User.id)
        .outerjoin(Campaign, Sponsor.id == Campaign.sponsor_id)
        .all()
    )
    
    return render_template('admin_dashboard.html', users=users, sponsors=sponsors)

@app.route('/sponsor_dashboard')
@login_required
def sponsor_dashboard():
    return render_template('sponsor_dashboard.html')

@app.route('/update_description', methods=['POST'])
@login_required
def update_description():
    new_description = request.form.get('description')
    if new_description:
        current_user.description = new_description
        db.session.commit()
        flash('Your description has been updated.', 'success')
    return redirect(url_for('influencer_dashboard'))

@app.route('/influencer_dashboard')
@login_required
def influencer_dashboard():
    return render_template('influencer_dashboard.html')

@app.route('/create_campaign', methods=['GET', 'POST'])
@login_required
def create_campaign():
    form = CampaignForm()
    if form.validate_on_submit():
        new_campaign = Campaign(
            sponsor_id=current_user.id, 
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            budget=form.budget.data,
            visibility=form.visibility.data,
            goals=form.goals.data
        )
        db.session.add(new_campaign)
        db.session.commit()
        return redirect(url_for('sponsor_dashboard'))
    return render_template('create_campaign.html', form=form)

@app.route('/manage_campaigns')
@login_required
def manage_campaigns():
    if current_user.role == 'sponsor':
        sponsor_id = current_user.id

        campaigns = Campaign.query.filter_by(sponsor_id=sponsor_id).all()

        joined_influencers = {}

        for campaign in campaigns:
            campaign_id = campaign.id
            influencers = User.query.join(CampaignInfluencer, User.id == CampaignInfluencer.influencer_id) \
                                    .filter(CampaignInfluencer.campaign_id == campaign_id).all()
            joined_influencers[campaign_id] = influencers

        return render_template('manage_campaign.html', campaigns=campaigns, joined_influencers=joined_influencers)
    else:
        flash('You do not have permission to view this page.', 'danger')
        return redirect(url_for('home'))

@app.route('/update_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def update_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.sponsor_id != current_user.id:
        flash('You do not have permission to update this campaign.', 'danger')
        return redirect(url_for('manage_campaigns'))

    form = CampaignForm(obj=campaign)
    if form.validate_on_submit():
        form.populate_obj(campaign)
        db.session.commit()
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('manage_campaigns'))

    return render_template('update_campaign.html', form=form)

@app.route('/delete_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.sponsor_id != current_user.id:
        flash('You do not have permission to delete this campaign.', 'danger')
        return redirect(url_for('manage_campaigns'))

    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully!', 'success')
    return redirect(url_for('manage_campaigns'))

@app.route('/join_campaign/<int:campaign_id>', methods=['POST'])
@login_required
def join_campaign(campaign_id):
    user = current_user
    if user.role != 'influencer':
        flash('Only influencers can join campaigns', 'danger')
        return redirect(url_for('view_campaigns'))

    campaign = Campaign.query.get_or_404(campaign_id)
    if not campaign:
        flash('Campaign not found', 'danger')
        return redirect(url_for('view_campaigns'))

    if user in campaign.influencers:
        flash('You have already joined this campaign', 'warning')
        return redirect(url_for('view_campaigns'))

    campaign_influencer = CampaignInfluencer(campaign_id=campaign_id, influencer_id=user.id)
    db.session.add(campaign_influencer)
    db.session.commit()

    flash('Joined campaign successfully', 'success')
    return redirect(url_for('view_campaigns'))

@app.route('/view_campaigns')
@login_required
def view_campaigns():
    campaigns = Campaign.query.filter_by(visibility='public').all()
    user = current_user
    joined_campaigns = {}

    if user and user.role == 'influencer':
        for campaign in campaigns:
            campaign_id = campaign.id
            joined_key = f'joined_campaign_{campaign_id}'

            if user in campaign.influencers:
                joined_campaigns[campaign_id] = True
            else:
                joined_campaigns[campaign_id] = False

    form = AdRequestForm() 

    return render_template('view_campaigns.html', campaigns=campaigns, current_user=user, joined_campaigns=joined_campaigns, form=form)

@app.route('/view_ad_requests')
@login_required
def view_ad_requests():
    if current_user.role == 'sponsor':
        ad_requests = AdRequest.query.join(Campaign, AdRequest.campaign_id == Campaign.id)\
                                    .filter(Campaign.sponsor_id == current_user.id)\
                                    .all()
    elif current_user.role == 'influencer':
        ad_requests = AdRequest.query.filter_by(influencer_id=current_user.id).all()
    else:
        ad_requests = AdRequest.query.all()
    
    return render_template('view_ad_requests.html', ad_requests=ad_requests)

@app.route('/approve_ad_request/<int:ad_request_id>', methods=['POST'])
@login_required
def approve_ad_request(ad_request_id):
    ad_request = AdRequest.query.get(ad_request_id)

    if not ad_request:
        flash('Ad request not found.', 'error')
        return redirect(url_for('view_ad_requests'))
    
    if current_user.id != ad_request.campaign.sponsor_id:
        flash('You are not authorized to approve this ad request.', 'error')
        return redirect(url_for('view_ad_requests'))
    ad_request.status = 'Approved'

    try:
        db.session.commit()
        flash('Ad request approved successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to approve ad request: {str(e)}', 'error')

    return redirect(url_for('view_ad_requests'))

@app.route('/reject_ad_request/<int:ad_request_id>', methods=['POST'])
@login_required
def reject_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    ad_request.status = 'Rejected'
    db.session.commit()
    
    flash('Ad request has been rejected successfully.', 'success')
    return redirect(url_for('view_ad_requests'))


@app.route('/negotiate_ad_request/<int:ad_request_id>', methods=['GET', 'POST'])
@login_required
def negotiate_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    form = AdRequestForm(obj=ad_request)

    if form.validate_on_submit():
        ad_request.content = form.content.data
        ad_request.payment_amount = form.payment_amount.data
        db.session.commit()

        flash('Ad request negotiation submitted successfully', 'success')
        return redirect(url_for('view_ad_requests'))
    return render_template('negotiate_ad_request.html', form=form, ad_request=ad_request)


@app.route('/submit_ad_request/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
def submit_ad_request(campaign_id):
    print("Reached submit_ad_request view function")
    form = AdRequestForm()
    campaign = Campaign.query.get_or_404(campaign_id)

    if form.validate_on_submit():
        content = form.content.data
        payment_amount = form.payment_amount.data

        ad_request = AdRequest(
            content=content,
            campaign_id=campaign.id,
            influencer_id=current_user.id,
            status='Pending',
            payment_amount=payment_amount
        )
        db.session.add(ad_request)
        db.session.commit()

        flash('Ad request submitted successfully', 'success')
        return redirect(url_for('view_ad_requests'))
    return render_template('submit_ad_request.html', form=form, campaign=campaign)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
