from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    # Relationships
    navigation_history = db.relationship('NavigationHistory', backref='user', lazy=True)
    settings = db.relationship('Settings', backref='user', uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class NavigationHistory(db.Model):
    __tablename__ = 'navigation_history'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    object_name = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    distance = db.Column(db.Float, nullable=True) # Estimated distance in meters
    direction = db.Column(db.String(20), nullable=True) # Left, Center, Right
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    voice_speed = db.Column(db.Integer, default=150) # Words per minute
    voice_volume = db.Column(db.Float, default=1.0) # 0.0 to 1.0
    alert_distance = db.Column(db.Float, default=2.0) # Alert threshold in meters
    theme = db.Column(db.String(20), default='dark')
