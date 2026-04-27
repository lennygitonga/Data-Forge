from app import db
from datetime import datetime
import enum

class JobStatus(enum.Enum):
    pending  = "pending"
    running  = "running"
    done     = "done"
    failed   = "failed"

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

    def __repr__(self):
        return f"<Job {self.id} — {self.site} → {self.email}>"