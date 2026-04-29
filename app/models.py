from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import enum


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(255), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    jobs       = db.relationship("Job", backref="owner", lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"


class JobStatus(enum.Enum):
    pending = "pending"
    running = "running"
    done    = "done"
    failed  = "failed"


class Job(db.Model):
    __tablename__ = "jobs"

    id          = db.Column(db.Integer, primary_key=True)
    site        = db.Column(db.String(500), nullable=False)
    email       = db.Column(db.String(255), nullable=False)
    query       = db.Column(db.Text, nullable=True)
    schedule    = db.Column(db.String(100), nullable=True)
    status      = db.Column(db.Enum(JobStatus), default=JobStatus.pending)
    result_url  = db.Column(db.Text, nullable=True)
    error_msg   = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    last_run_at = db.Column(db.DateTime, nullable=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Job {self.id} — {self.site} → {self.email}>"