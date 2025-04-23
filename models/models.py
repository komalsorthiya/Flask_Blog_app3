# Import the tools we need to work with the database and handle user authentication
from flask_sqlalchemy import SQLAlchemy  # This helps us talk to the database
from flask_login import UserMixin  # This helps us handle user login
from werkzeug.security import generate_password_hash, check_password_hash  # These help us keep passwords safe
from datetime import datetime, timedelta  # These help us work with dates and times
import secrets  # This helps us create secure random tokens

# Create a new database connection
db = SQLAlchemy()

# This class defines what information we store about each user
class User(UserMixin, db.Model):
    # Each user has these pieces of information:
    id = db.Column(db.Integer, primary_key=True)  # A unique number for each user
    username = db.Column(db.String(80), unique=True, nullable=False)  # Their chosen username (must be unique)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Their email address (must be unique)
    password_hash = db.Column(db.String(128))  # Their password (stored safely, not in plain text)
    posts = db.relationship('Post', backref='author', lazy=True)  # Links to all their blog posts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When they created their account
    reset_tokens = db.relationship('PasswordResetToken', backref='user', lazy=True)  # Links to their password reset requests

    # This function safely stores a new password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  # Converts password to a safe format

    # This function checks if a password is correct
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  # Compares password with stored version

    # This function creates a special code for resetting password
    def generate_reset_token(self):
        token = secrets.token_urlsafe(32)  # Creates a random, secure code
        reset_token = PasswordResetToken(token=token, user=self)  # Saves the code
        db.session.add(reset_token)  # Adds it to the database
        db.session.commit()  # Saves the changes
        return token  # Returns the code to be sent to user

# This class defines what information we store about each blog post
class Post(db.Model):
    # Each post has these pieces of information:
    id = db.Column(db.Integer, primary_key=True)  # A unique number for each post
    title = db.Column(db.String(100), nullable=False)  # The post's title
    content = db.Column(db.Text, nullable=False)  # The post's content
    image_filename = db.Column(db.String(255))  # The name of any image attached to the post
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When the post was created
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Who wrote the post

# This class handles password reset requests
class PasswordResetToken(db.Model):
    # Each reset request has these pieces of information:
    id = db.Column(db.Integer, primary_key=True)  # A unique number for each request
    token = db.Column(db.String(100), unique=True, nullable=False)  # The special code sent to user
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Which user requested the reset
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When the request was made
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(hours=1))  # When the code will stop working

    # This function checks if the reset code is still good to use
    def is_valid(self):
        return datetime.utcnow() < self.expires_at  # Returns true if the code hasn't expired yet 