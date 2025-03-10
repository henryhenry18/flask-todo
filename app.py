from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import sqlite3
from flask import Flask
from datetime import datetime
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'  # Ensure this is correct
app.config["SECRET_KEY"] = "your_secret_key"  # Change this to a secure key
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# Initialize database
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS tasks 
                      (id INTEGER PRIMARY KEY, task TEXT, completed BOOLEAN)''')
    conn.commit()
    conn.close()

init_db()  # Run once to create the DB

# Home Route - Show Tasks
@app.route("/")
def index():
    tasks = Task.query.all()
    return render_template("index.html", tasks=tasks)


# Add Task
# ✅ Route to handle form submission
@app.route("/add", methods=["POST"])
def add_task():
    task_text = request.form.get("task_text")

    print("🔥 Debug: Task received ->", task_text)  # ✅ Print the received task

    if not task_text or not task_text.strip():  # 🔴 Check for empty tasks
        flash("Error: Task cannot be empty!", "danger")
        return redirect(url_for("index"))

    new_task = Task(task=task_text, user_id=current_user.id)  # ✅ Make sure user_id is set
    db.session.add(new_task)
    db.session.commit()

    flash("Task added successfully!", "success")
    return redirect(url_for("index"))

@app.route("/complete/<int:task_id>")
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        task.completed = True
        db.session.commit()
    return redirect(url_for("index"))



# Delete Task
@app.route("/delete/<int:task_id>")
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
    return redirect(url_for("index"))


# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Define how to load users from the database
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # ✅ This must be in app.py


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = bcrypt.generate_password_hash(request.form["password"]).decode("utf-8")

        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Username already exists. Try another!", "danger")
            return redirect(url_for("signup"))

        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password!", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/")
def home():
    return "Flask App is Running!"

if __name__ == "__main__":
    app.run(debug=True)  # ✅ Enables error messages in the browser
