import os
from flask import Flask, redirect, url_for, render_template_string
from replit import web

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# This is the correct way to initialize Replit Auth
auth = web.Auth(app)

# Simple login page
HOME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Replit Auth Example</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background-color: #0066ff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px;
        }
        .welcome {
            margin-top: 30px;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <h1>Replit Auth Example</h1>
    
    {% if auth.is_authenticated %}
        <div class="welcome">
            <h2>Welcome, {{ auth.name }}!</h2>
            <p>You are logged in with Replit Auth.</p>
            <a href="{{ url_for('protected_page') }}" class="btn">Go to Protected Page</a>
            <a href="{{ url_for('logout') }}" class="btn">Logout</a>
        </div>
    {% else %}
        <p>You are not logged in.</p>
        <a href="{{ url_for('login') }}" class="btn">Sign in with Replit</a>
    {% endif %}
</body>
</html>
"""

PROTECTED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Protected Page</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            text-align: center;
        }
        .btn {
            display: inline-block;
            padding: 10px 20px;
            background-color: #0066ff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px;
        }
        .content {
            margin-top: 30px;
            padding: 20px;
            background-color: #f5f5f5;
            border-radius: 10px;
        }
    </style>
</head>
<body>
    <h1>Protected Page</h1>
    
    <div class="content">
        <h2>Hello {{ auth.name }}!</h2>
        <p>This page is only visible to logged-in users.</p>
        <p>Your Replit ID: {{ auth.id }}</p>
        <a href="{{ url_for('index') }}" class="btn">Back to Home</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HOME_TEMPLATE)

@app.route('/login')
def login():
    # The correct way to redirect to Replit login
    return redirect(f"https://replit.com/auth_with_repl_site?domain={web.get_origin()}")

@app.route('/protected')
def protected_page():
    # Check if user is authenticated
    if not auth.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template_string(PROTECTED_TEMPLATE)

@app.route('/logout')
def logout():
    # Replit Auth doesn't have a built-in logout mechanism like Flask-Login
    # We can redirect to Replit's logout page
    return redirect("https://replit.com/logout")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)