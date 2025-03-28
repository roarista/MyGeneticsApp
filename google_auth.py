import json
import os

import requests
from flask import Blueprint, redirect, request, url_for
from flask_login import login_user, logout_user, login_required
from oauthlib.oauth2 import WebApplicationClient

from app import db
from models import User

# Google OAuth client configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

# Replit domain for callback URL
REPLIT_DOMAIN = os.environ.get("REPLIT_DEV_DOMAIN")
REDIRECT_URL = f'https://{REPLIT_DOMAIN}/google_login/callback'

# Print setup instructions
print(f"""
To enable Google authentication:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create a new OAuth 2.0 Client ID
3. Add {REDIRECT_URL} to Authorized redirect URIs

For detailed instructions, see:
https://docs.replit.com/additional-resources/google-auth-in-flask#set-up-your-oauth-app--client
""")

# Initialize client based on availability of client ID
client = None
if GOOGLE_CLIENT_ID:
    client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Create Blueprint
google_auth = Blueprint("google_auth", __name__)


@google_auth.route("/google_login")
def login():
    """Start Google OAuth login process"""
    if not client:
        from flask import flash
        flash('Google OAuth is not configured yet. Please use email login instead.', 'warning')
        return redirect(url_for('login'))
        
    try:
        # Get Google's OAuth 2.0 provider configuration
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Prepare request URI for Google
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            # Replacing http:// with https:// for security
            redirect_uri=request.base_url.replace("http://", "https://") + "/callback",
            scope=["openid", "email", "profile"],
        )
        return redirect(request_uri)
    except Exception as e:
        from flask import flash
        flash(f'Error connecting to Google: {str(e)}', 'danger')
        return redirect(url_for('login'))


@google_auth.route("/google_login/callback")
def callback():
    """Handle the Google OAuth 2.0 callback"""
    if not client:
        from flask import flash
        flash('Google OAuth is not configured yet. Please use email login instead.', 'warning')
        return redirect(url_for('login'))
        
    try:
        # Get authorization code from Google
        code = request.args.get("code")
        
        if not code:
            from flask import flash
            flash('Authentication failed - no authorization code received from Google.', 'danger')
            return redirect(url_for('login'))
        
        # Get token endpoint from Google
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]

        # Prepare token request
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            # Ensure we use HTTPS for the authorization response
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=request.base_url.replace("http://", "https://"),
            code=code,
        )
        
        # Exchange authorization code for tokens
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse token response
        client.parse_request_body_response(json.dumps(token_response.json()))

        # Get user info from Google
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)

        # Verify user info
        userinfo = userinfo_response.json()
        if not userinfo.get("email_verified"):
            from flask import flash
            flash('Google could not verify your email address.', 'danger')
            return redirect(url_for('login'))

        # Get user identity from Google response
        google_id = userinfo["sub"]
        user_email = userinfo["email"]
        user_name = userinfo["given_name"]

        # Create or update user in database
        user = User.query.filter_by(email=user_email).first()
        if not user:
            user = User(
                username=user_name,
                email=user_email,
                profile_image=userinfo.get("picture")
            )
            db.session.add(user)
            db.session.commit()

        # Log in the user
        login_user(user)
        flash(f'Welcome, {user_name}! You have successfully logged in with Google.', 'success')
        return redirect(url_for("profile"))
        
    except Exception as e:
        from flask import flash
        flash(f'Error during Google authentication: {str(e)}', 'danger')
        return redirect(url_for('login'))


@google_auth.route("/logout")
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    return redirect(url_for("index"))