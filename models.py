from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    registered_with_google = db.Column(db.Boolean, default=False)

    # New fields
    first_name = db.Column(db.String(100), nullable=True)  # You can adjust nullability as needed
    last_name = db.Column(db.String(100), nullable=True)

    verification_code = db.Column(db.String(6), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)


class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_name = db.Column(db.String(150), nullable=False)
    result = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
