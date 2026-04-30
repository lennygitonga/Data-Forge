import os
from flask import Blueprint, redirect, url_for, flash
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, current_user
from app import db, bcrypt
from app.models import User

google_auth = Blueprint("google_auth", __name__)

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    scope=["openid", "https://www.googleapis.com/auth/userinfo.email",
           "https://www.googleapis.com/auth/userinfo.profile"],
    redirect_to="google_auth.google_login_callback"
)


@google_auth.record_once
def register_google_bp(state):
    state.app.register_blueprint(google_bp, url_prefix="/login")


@google_auth.route("/login/google/callback")
def google_login_callback():
    if not google.authorized:
        flash("Google login failed. Please try again.", "error")
        return redirect(url_for("auth.login"))

    try:
        resp = google.get("/oauth2/v2/userinfo")
        if not resp.ok:
            flash("Could not fetch your Google account info.", "error")
            return redirect(url_for("auth.login"))

        google_info = resp.json()
        email = google_info["email"]
        name  = google_info.get("name", email.split("@")[0])

        # check if user already exists
        user = User.query.filter_by(email=email).first()

        if not user:
            # create new user from google account
            hashed_pw = bcrypt.generate_password_hash(
                os.urandom(24).hex()
            ).decode("utf-8")

            user = User(
                name=name,
                email=email,
                password=hashed_pw
            )
            db.session.add(user)
            db.session.commit()
            flash(f"Welcome to Data-Forge, {name}!", "success")
        else:
            flash(f"Welcome back, {name}!", "success")

        login_user(user)
        return redirect(url_for("main.home"))

    except Exception as e:
        flash(f"Google login error: {str(e)}", "error")
        return redirect(url_for("auth.login"))