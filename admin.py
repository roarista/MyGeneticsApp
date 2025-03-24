"""
Admin utilities for MyGenetics application.

This module provides routes and functions for administrative tasks
like database initialization and user management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from app import db
from models import User, NotificationSetting, PrivacySetting

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/init_db')
def init_db():
    """Initialize database with essential data."""
    # Create tables if they don't exist
    db.create_all()
    
    # Create a demo admin user if it doesn't exist
    admin_email = 'admin@mygenetics.com'
    admin = User.query.filter_by(email=admin_email).first()
    
    if not admin:
        admin = User(
            username='Admin',
            email=admin_email,
            height_cm=180,
            weight_kg=80,
            gender='male',
            experience_level='advanced'
        )
        admin.set_password('adminpass')  # In production, use a secure password
        db.session.add(admin)
        db.session.commit()  # Commit first to get the admin.id
        
        # Create notification settings for admin
        notif_settings = NotificationSetting(user_id=admin.id)
        db.session.add(notif_settings)
        
        # Create privacy settings for admin
        privacy_settings = PrivacySetting(user_id=admin.id)
        db.session.add(privacy_settings)
        
        db.session.commit()  # Commit the settings
        flash('Admin user created successfully.', 'success')
    else:
        flash('Admin user already exists.', 'info')
    
    # Create a demo user if it doesn't exist
    demo_email = 'demo@mygenetics.com'
    demo_user = User.query.filter_by(email=demo_email).first()
    
    if not demo_user:
        demo_user = User(
            username='Demo User',
            email=demo_email,
            height_cm=175,
            weight_kg=70,
            gender='male',
            experience_level='intermediate',
            bio='This is a demo user account for testing the MyGenetics app.'
        )
        demo_user.set_password('demopass')  # In production, use a secure password
        db.session.add(demo_user)
        db.session.commit()  # Commit first to get the demo_user.id
        
        # Create notification settings for demo user
        notif_settings = NotificationSetting(user_id=demo_user.id)
        db.session.add(notif_settings)
        
        # Create privacy settings for demo user
        privacy_settings = PrivacySetting(user_id=demo_user.id)
        db.session.add(privacy_settings)
        
        db.session.commit()  # Commit the settings
        flash('Demo user created successfully.', 'success')
    else:
        flash('Demo user already exists.', 'info')
    
    return redirect(url_for('index'))

@admin_bp.route('/reset_db')
def reset_db():
    """Reset database (drop all tables and recreate)."""
    db.drop_all()
    db.create_all()
    flash('Database has been reset.', 'success')
    return redirect(url_for('admin.init_db'))