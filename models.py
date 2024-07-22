from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  
    description = db.Column(db.String(255), nullable=True)
    campaigns = db.relationship('Campaign', secondary='campaign_influencer', backref=db.backref('influencers', lazy='dynamic'))

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    industry = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Sponsor('{self.company_name}')"

class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(120), nullable=False)
    niche = db.Column(db.String(120), nullable=False)
    reach = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Influencer('{self.name}', '{self.category}')"

class Campaign(db.Model):
    __tablename__ = 'campaign'
    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(50), nullable=False)
    goals = db.Column(db.Text, nullable=True)

class CampaignInfluencer(db.Model):
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), primary_key=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)


    def __repr__(self):
        return f"CampaignInfluencer(campaign_id={self.campaign_id}, influencer_id={self.influencer_id})"


class AdRequest(db.Model):
    __tablename__ = 'ad_request'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    payment_amount = db.Column(db.Float)
    campaign = db.relationship('Campaign', backref=db.backref('ad_requests', lazy=True))
    influencer = db.relationship('Influencer', backref=db.backref('ad_requests', lazy=True))



