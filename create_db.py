from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    db.drop_all()
    db.create_all()

print("Database tables created successfully.")
