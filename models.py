"""
Database models for the MyGenetics fitness app.

This module defines the database schema for storing user information,
body measurements, analysis results, and fitness recommendations.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.postgresql import JSON

# Avoid circular imports by importing db this way
from app import db


class User(UserMixin, db.Model):
    """User model for authentication and profile information."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Profile information
    bio = db.Column(db.Text)
    profile_image = db.Column(db.String(256))  # Path to profile image
    
    # Body measurements
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    gender = db.Column(db.String(16))
    experience_level = db.Column(db.String(32))
    
    # Relationships
    analyses = db.relationship('Analysis', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    body_scans = db.relationship('BodyScan3D', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    workout_plans = db.relationship('WorkoutPlan', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Analysis(db.Model):
    """Model for storing body analysis results."""
    
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Analysis type (image or 3D scan)
    analysis_type = db.Column(db.String(32), default='image')
    
    # Image path (if applicable)
    image_path = db.Column(db.String(256))
    
    # Analysis results
    body_fat_percentage = db.Column(db.Float)
    muscle_building_potential = db.Column(db.Float)
    body_type = db.Column(db.String(32))
    
    # JSON fields for detailed results
    traits = db.Column(JSON)
    recommendations = db.Column(JSON)
    measurements = db.Column(JSON)
    
    def __repr__(self):
        return f'<Analysis {self.id} for User {self.user_id}>'


class BodyScan3D(db.Model):
    """Model for storing 3D body scan data."""
    
    __tablename__ = 'body_scans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    scan_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # File path
    file_path = db.Column(db.String(256))
    file_format = db.Column(db.String(16))
    
    # Measurements extracted from 3D scan
    measurements = db.Column(JSON)
    body_composition = db.Column(JSON)
    
    # Visualization paths
    visualization_front = db.Column(db.String(256))
    visualization_side = db.Column(db.String(256))
    visualization_3d = db.Column(db.String(256))
    
    # Relationship to analysis
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id', ondelete='SET NULL'), nullable=True)
    analysis = db.relationship('Analysis', backref=db.backref('scan', uselist=False))
    
    def __repr__(self):
        return f'<BodyScan3D {self.id} for User {self.user_id}>'


class WorkoutPlan(db.Model):
    """Model for storing personalized workout plans."""
    
    __tablename__ = 'workout_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Plan details
    goal = db.Column(db.String(32))  # lose_fat, gain_muscle, maintain, recomp
    duration_weeks = db.Column(db.Integer, default=8)
    training_split = db.Column(db.String(32))  # push_pull_legs, etc.
    
    # Plan content
    workout_schedule = db.Column(JSON)  # Detailed workout schedule
    nutrition_plan = db.Column(JSON)  # Nutrition recommendations
    
    # Relationships
    analysis = db.relationship('Analysis', backref=db.backref('workout_plan', uselist=False))
    
    def __repr__(self):
        return f'<WorkoutPlan {self.id} for User {self.user_id}>'


class MeasurementLog(db.Model):
    """Model for tracking body measurements over time."""
    
    __tablename__ = 'measurement_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    log_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Basic measurements
    weight_kg = db.Column(db.Float)
    body_fat_percentage = db.Column(db.Float)
    
    # Circumference measurements
    chest_cm = db.Column(db.Float)
    waist_cm = db.Column(db.Float)
    hips_cm = db.Column(db.Float)
    arms_cm = db.Column(db.Float)  # Average of both arms
    thighs_cm = db.Column(db.Float)  # Average of both thighs
    
    # Performance metrics
    notes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<MeasurementLog {self.id} for User {self.user_id}>'


class NotificationSetting(db.Model):
    """Model for user notification preferences."""
    
    __tablename__ = 'notification_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Email notifications
    email_updates = db.Column(db.Boolean, default=True)
    email_progress = db.Column(db.Boolean, default=True)
    email_tips = db.Column(db.Boolean, default=True)
    
    # In-app notifications
    app_reminders = db.Column(db.Boolean, default=True)
    app_milestones = db.Column(db.Boolean, default=True)
    app_updates = db.Column(db.Boolean, default=True)
    
    # Frequency settings
    notification_frequency = db.Column(db.String(16), default='weekly')  # daily, weekly, monthly
    
    def __repr__(self):
        return f'<NotificationSetting for User {self.user_id}>'


class PrivacySetting(db.Model):
    """Model for user privacy settings."""
    
    __tablename__ = 'privacy_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Data privacy
    data_storage_duration = db.Column(db.String(32), default='indefinite')  # indefinite, 1-year, 6-months, 3-months
    profile_visibility = db.Column(db.String(16), default='private')  # private, public
    share_progress = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<PrivacySetting for User {self.user_id}>'