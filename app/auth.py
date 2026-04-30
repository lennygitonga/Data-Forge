import os
from flask import Blueprint, redirect, url_for, flash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user
from app import db, bcrypt
from app.models import User

google_auth = Blueprint("google_auth", __name__)

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["openid",
           "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"]
)


@google_auth.record_once
def register_google_bp(state):
    state.app.register_blueprint(google_bp, url_prefix="/login")


from flask_dance.consumer import oauth_authorized
from flask_dance.contrib.google import google as google_oauth

@oauth_authorized.connect_via(google_bp)
def google_logged_in(blueprint, token):
    if not token:
        flash("Google login failed.", "error")
        return False

    resp = blueprint.session.get("/oauth2/v2/userinfo")
    if not resp.ok:
        flash("Could not fetch Google account info.", "error")
        return False

    google_info = resp.json()
    email = google_info["email"]
    name  = google_info.get("name", email.split("@")[0])

    user = User.query.filter_by(email=email).first()

    if not user:
        hashed_pw = bcrypt.generate_password_hash(
            os.urandom(24).hex()
        ).decode("utf-8")
        user = User(name=name, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f"Welcome to Data-Forge, {name}!", "success")
    else:
        flash(f"Welcome back, {name}!", "success")

    login_user(user)
    return False