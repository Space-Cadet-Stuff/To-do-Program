from flask import Flask, render_template, request, session, redirect, url_for, flash
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from setup_db import User, ToDo
from datetime import datetime

app = Flask(__name__)# Creates the Flask app
app.secret_key = 'erjopur[ur=0gr=0rbu-ie-g29-be29u'# Secret key for the session. Generated by mashing the keyboard.


engine = create_engine('sqlite:///todo.db')# Connects to the database
Session = sessionmaker(bind=engine)
db_session = Session()


@app.route('/')# Define the index route
def index():
    return render_template('index.html')# Renders the index page


@app.route('/login', methods=["GET", "POST"])# Define the login route
def login():
    if request.method == "POST":# Get form data
        username = request.form.get('username')
        password = request.form.get('password')

        user = db_session.query(User).filter_by(username=username).first()# Check if the user exists and/or password is correct
        if user and check_password_hash(user.password, password):# If correct, begins session with user id and username
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Logged in successfully", "info")
            return redirect(url_for('dashboard'))# Redirects to the dashboard
        else:# If incorrect, flashes an error message
            flash("Invalid username or password", "error")

    return render_template('login.html')# Renders the login page


@app.route('/signup', methods=["GET", "POST"])# Define the signup route
def signup():
    if request.method == "POST":# Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = db_session.query(User).filter((User.username == username) | (User.email == email)).first()# Check if username or email already exists
        if existing_user:
            flash("Username or email already exists. Please choose another.", "error")
            return redirect(url_for('signup'))
        
        password = generate_password_hash(password)# Hash the password for security
        
        new_user = User(username = username, email = email, password = password)# Create a new user instance
        
        db_session.add(new_user)# Add and commit the new user to the database
        db_session.commit()
        
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for('login'))# Redirect to the login page after successful signup
    
    return render_template('signup.html')# Render the signup page


@app.route('/dashboard')# Define the dashboard route
def dashboard():
    if "user_id" not in session:# Check if the user is logged in
        flash("You need to login first", "warning")
        return redirect(url_for('login'))  # Redirect to the login page if the user is not logged in
    
    if 'first_login' in session and session['first_login']:# Check if it's the first time visiting the dashboard after login or logout
        flash("Welcome back, {}!".format(session["username"]), "info")
        session['first_login'] = False  # Set 'first_login' to False after showing the message

    todos = db_session.query(ToDo).filter(ToDo.user_id == session["user_id"]).all()# Get all tasks associated with the current user
    
    return render_template('dashboard.html', user_id=session["user_id"], username=session["username"], todos = todos)# Render the dashboard page and store the current user's id and username in the session


@app.route('/create', methods=["GET", "POST"])# Define the create route
def create():
    if "user_id" not in session:# Checks if the user is logged in, and redirects to login if not
        flash("You need to login first", "warning")
        return redirect(url_for('login'))# Redirects to the login pages
    
    if request.method == "POST":# Extract data from the form
        title = request.form.get('title')
        category = request.form.get('category')
        date_str = request.form.get('date')
        description = request.form.get('description')

        date = datetime.strptime(date_str, "%Y-%m-%d")# Convert the date string to a datetime object

        new_task = ToDo(# Create a new ToDo instance
            title = title,
            category = category,
            date = date,
            description = description,
            user_id = session["user_id"]# Associate task with logged-in user
        )

        db_session.add(new_task)# Add to database and commit
        db_session.commit()

        flash("Task created successfully!", "success")

    return render_template('create.html', user_id=session["user_id"], username=session["username"])# Renders the create page and stores the current users id and username in the session


@app.route('/logout')# Defines the logout route
def logout():
    session.clear()# Clears the session
    flash("You have been logged out", "info")
    return redirect(url_for('index'))# Redirects to the index page


@app.route('/delete/<task_id>', methods=["POST"])# Define the delete route
def delete(task_id):
    if "user_id" not in session:# Check if the user is logged in
        flash("You need to login first", "warning")
        return redirect(url_for('login'))# Redirect to the login page
    
    task = db_session.query(ToDo).filter_by(id=task_id, user_id=session["user_id"]).first()# Check if the task exists and the user has permission to delete it
    if task:# Deletes select task and flashes a success message
        db_session.delete(task)
        db_session.commit()
        flash("Task deleted successfully!", "success")
    else:# Flashes an error message if the task is not found or the user does not have permission to delete it
        flash("Task not found or you do not have permission to delete it", "error")
    
    return redirect(url_for('dashboard'))# Redirects to the dashboard


@app.route('/complete/<task_id>', methods=["POST"])# Define the complete route
def complete(task_id):
    if "user_id" not in session:# Check if the user is logged in
        flash("You need to login first", "warning")
        return redirect(url_for('login'))# Redirect to the login page
    
    task = db_session.query(ToDo).filter_by(id=task_id, user_id=session["user_id"]).first()# Check if the task exists and the user has permission to complete it
    if task:# Marks the task as completed and flashes a success message
        task.done = True
        db_session.commit()
        flash("Task marked as completed!", "success")
    else:# Flashes an error message if the task is not found or the user does not have permission to complete it
        flash("Task not found or you do not have permission to complete it", "error")
    
    return redirect(url_for('dashboard'))# Redirects to the dashboard


@app.route('/task/<int:task_id>')
def task(task_id):
    if "user_id" not in session:  # Ensure the user is logged in
        flash("You need to login first", "warning")
        return redirect(url_for('login'))  # Redirect to login if not

    task = db_session.query(ToDo).filter_by(id=task_id, user_id=session["user_id"]).first()# Fetch the task from the database
    
    if not task:  # Handle cases where the task is not found
        flash("Task not found or you do not have permission to view it", "error")
        return redirect(url_for('dashboard'))  # Redirect to the dashboard

    return render_template('task.html', task=task)  # Render the task details page


@app.route('/incomplete/<task_id>', methods=["POST"])  # New route for marking as incomplete
def incomplete(task_id):
    if "user_id" not in session:
        flash("You need to login first", "warning")
        return redirect(url_for('login'))

    task = db_session.query(ToDo).filter_by(id=task_id, user_id=session["user_id"]).first()
    if task:
        task.done = False  # Mark the task as incomplete
        db_session.commit()
        flash("Task marked as incomplete!", "success")
    else:
        flash("Task not found or you do not have permission to modify it", "error")
    
    return redirect(url_for('dashboard'))


@app.route('/edit/<int:task_id>', methods=["GET", "POST"])# Define the edit route
def edit(task_id):
    if "user_id" not in session:# Ensure the user is logged in
        flash("You need to login first", "warning")
        return redirect(url_for('login'))# Redirect to login if not logged in

    task = db_session.query(ToDo).filter_by(id=task_id, user_id=session["user_id"]).first()# Fetch the task from the database

    if not task:# If the task doesn't exist or the user doesn't have permission
        flash("Task not found or you do not have permission to edit it", "error")
        return redirect(url_for('dashboard'))  # Redirect to the dashboard

    if request.method == "POST":# If the form is submitted
        title = request.form.get('title')
        category = request.form.get('category')
        date_str = request.form.get('date')
        description = request.form.get('description')

        date = datetime.strptime(date_str, "%Y-%m-%d")# Convert the date string to a datetime object

        task.title = title# Update the task attributes
        task.category = category
        task.date = date
        task.description = description

        db_session.commit()# Commit the changes to the database

        flash("Task updated successfully!", "success")
        return redirect(url_for('dashboard'))# Redirect to the dashboard

    return render_template('edit.html', task=task)# Render the edit form with the task data


@app.template_filter('days_left')# Custom Jinja filter to calculate the number of days left for a task
def days_left(due_date):
    today = datetime.now()  # Get today's date and time
    delta = due_date - today  # Calculate the difference
    if delta.days > 0:  # If the due date is in the future
        return delta.days  # Return the number of days left
    elif delta.days+1 == 0:  # If the due date is today
        return "Today"
    else:  # If the task is overdue
        return "Overdue"


app.run(debug=True)# Runs the app in debug mode