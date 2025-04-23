# Import all the tools we need to make our blog work
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory  # These help us create web pages and handle user actions
from flask_login import LoginManager, login_user, login_required, logout_user, current_user  # These help us manage user login
import os  # This helps us work with files and folders
from dotenv import load_dotenv  # This helps us read secret settings from a file
from models.models import db, User, Post, PasswordResetToken  # These are our database models
from werkzeug.utils import secure_filename  # This helps us safely handle uploaded files
from utils.email import send_reset_email

# Load our secret settings from the .env file
load_dotenv()

# Create our blog application
app = Flask(__name__)


# Set up all our application settings
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')  # A secret code to keep our app secure
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost/blog_db')  # Where to find our database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # This helps our app run faster
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Where to store uploaded images
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maximum size for uploaded files (16MB)

# Make sure the folder for uploaded images exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Set up our database and login system
db.init_app(app)  # Connect to the database
login_manager = LoginManager()  # Create the login manager
login_manager.init_app(app)  # Connect it to our app
login_manager.login_view = 'login'  # Tell it which page to show when someone needs to log in


# This function helps Flask-Login find users
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Find a user by their ID number


# This route lets users see uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)  # Send the image file to the user


# This is our homepage - it shows all blog posts
@app.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()  # Get all posts, newest first
    return render_template('index.html', posts=posts)  # Show the homepage with the posts


# This route handles new user registration
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':  # If someone is submitting the signup form
        username = request.form.get('username')  # Get their chosen username
        email = request.form.get('email')  # Get their email
        password = request.form.get('password')  # Get their password
        
        # Check if username is already taken
        if User.query.filter_by(username=username).first():
            flash('Username already exists')  # Show an error message
            return redirect(url_for('signup'))  # Send them back to signup
        
        # Check if email is already used
        if User.query.filter_by(email=email).first():
            flash('Email already exists')  # Show an error message
            return redirect(url_for('signup'))  # Send them back to signup
        
        # Create the new user
        user = User(username=username, email=email)
        user.set_password(password)  # Save their password safely
        db.session.add(user)  # Add them to the database
        db.session.commit()  # Save the changes
        
        flash('Account created successfully!')  # Show a success message
        return redirect(url_for('login'))  # Send them to the login page
    
    return render_template('signup.html')  # Show the signup form


# This route handles user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # If someone is submitting the login form
        username = request.form.get('username')  # Get their username
        password = request.form.get('password')  # Get their password
        user = User.query.filter_by(username=username).first()  # Try to find their account
        
        # Check if their password is correct
        if user and user.check_password(password):
            login_user(user)  # Log them in
            return redirect(url_for('index'))  # Send them to the homepage
        
        flash('Invalid username or password')  # Show an error message
    return render_template('login.html')  # Show the login form


# This route handles password reset requests
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':  # If someone is submitting the forgot password form
        email = request.form.get('email')  # Get their email
        user = User.query.filter_by(email=email).first()  # Try to find their account
        
        # If we found their account
        if user:
            token = user.generate_reset_token()  # Create a reset code
            send_reset_email(user, token)  # Send them an email with the code
            flash('Password reset instructions have been sent to your email.')  # Show a success message
            return redirect(url_for('login'))  # Send them to the login page
        
        flash('No account found with that email address.')  # Show an error message
    return render_template('forgot_password.html')  # Show the forgot password form


# This route handles the actual password reset
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Check if the reset code is valid
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    
    # If the code is invalid or expired
    if not reset_token or not reset_token.is_valid():
        flash('Invalid or expired password reset link.')  # Show an error message
        return redirect(url_for('forgot_password'))  # Send them back to request a new code
    
    if request.method == 'POST':  # If they're submitting a new password
        password = request.form.get('password')  # Get their new password
        user = reset_token.user  # Find their account
        user.set_password(password)  # Save their new password
        db.session.delete(reset_token)  # Delete the used reset code
        db.session.commit()  # Save the changes
        
        flash('Your password has been reset successfully.')  # Show a success message
        return redirect(url_for('login'))  # Send them to the login page
    
    return render_template('reset_password.html', token=token)  # Show the reset password form


# This route handles user logout
@app.route('/logout')
@login_required  # Make sure they're logged in first
def logout():
    logout_user()  # Log them out
    return redirect(url_for('index'))  # Send them to the homepage


# This route handles creating new blog posts
@app.route('/create_post', methods=['GET', 'POST'])
@login_required  # Make sure they're logged in first
def create_post():
    if request.method == 'POST':  # If they're submitting a new post
        title = request.form.get('title')  # Get the post title
        content = request.form.get('content')  # Get the post content
        image = request.files.get('image')  # Get any uploaded image
        
        # Create the new post
        post = Post(title=title, content=content, author=current_user)
        
        # If they uploaded an image
        if image and image.filename:
            filename = secure_filename(image.filename)  # Make the filename safe
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Where to save it
            image.save(image_path)  # Save the image
            post.image_filename = filename  # Remember the image filename
        
        db.session.add(post)  # Add the post to the database
        db.session.commit()  # Save the changes
        
        flash('Post created successfully!')  # Show a success message
        return redirect(url_for('index'))  # Send them to the homepage
    
    return render_template('create_post.html')  # Show the create post form



# This runs our application
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all the database tables
    app.run(debug=True)  # Start the web server 