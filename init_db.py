#!/usr/bin/env python3
"""
Database initialization script for MoreAI authentication system.
Run this script to create the database and tables.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from models import db, User
from werkzeug.security import generate_password_hash

def create_app():
    """Create Flask app for database operations"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    return app

def init_database():
    """Initialize the database with tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")
        
        # Check if admin user exists
        admin_user = User.query.filter_by(username='admin').first()
        
        if not admin_user:
            print("Creating admin user...")
            
            # Create admin user
            admin = User(
                username='admin',
                is_admin=True,
                is_active=True
            )
            admin.set_password('Admin123!')  # Change this password!
            
            db.session.add(admin)
            db.session.commit()
            
            print("Admin user created successfully!")
            print("Username: admin")
            print("Password: Admin123!")
            print("IMPORTANT: Change the admin password after first login!")
        else:
            print("Admin user already exists.")
        
        print("\nDatabase initialization completed!")
        print("You can now start your Flask application.")

def create_sample_users():
    """Create some sample users for testing"""
    app = create_app()
    
    with app.app_context():
        print("Creating sample users...")
        
        # Sample users
        sample_users = [
            {
                'username': 'john_doe',
                'password': 'Test123!'
            },
            {
                'username': 'jane_smith',
                'password': 'Test123!'
            }
        ]
        
        for user_data in sample_users:
            if not User.query.filter_by(username=user_data['username']).first():
                user = User(
                    username=user_data['username']
                )
                user.set_password(user_data['password'])
                
                db.session.add(user)
                print(f"Created user: {user_data['username']}")
            else:
                print(f"User {user_data['username']} already exists.")
        
        db.session.commit()
        print("Sample users created successfully!")

if __name__ == '__main__':
    print("MoreAI Database Initialization")
    print("=" * 40)
    
    # Check if database URL is configured
    if not os.environ.get('DATABASE_URL'):
        print("WARNING: DATABASE_URL environment variable not set.")
        print("Using default SQLite database.")
        print("For PostgreSQL, set DATABASE_URL environment variable.")
        print()
    
    try:
        init_database()
        
        # Ask if user wants to create sample users
        response = input("\nWould you like to create sample users? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            create_sample_users()
        
        print("\nSetup complete! You can now run your Flask application.")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        sys.exit(1) 