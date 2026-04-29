from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.scraper import fetch_page
from app.ai import resolve_site, summarise_content
from app.emailer import send_report_email
from app import db
from app.models import Job, JobStatus
from datetime import datetime

main = Blueprint("main", __name__)


@main.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))
    return redirect(url_for("auth.login"))


@main.route("/dashboard")
@login_required
def home():
    jobs = Job.query.filter_by(user_id=current_user.id)\
               .order_by(Job.created_at.desc()).limit(5).all()
    return render_template("dashboard/home.html", jobs=jobs)


@main.route("/jobs")
@login_required
def jobs():
    all_jobs = Job.query.filter_by(user_id=current_user.id)\
                  .order_by(Job.created_at.desc()).all()
    return render_template("dashboard/jobs.html", jobs=all_jobs)


@main.route("/jobs/<int:job_id>")
@login_required
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template("dashboard/job_detail.html", job=job)


@main.route("/jobs/<int:job_id>/delete", methods=["POST"])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    flash("Job deleted.", "success")
    return redirect(url_for("main.jobs"))


@main.route("/settings")
@login_required
def settings():
    return render_template("settings.html")


@main.route("/scrape", methods=["POST"])
@login_required
def scrape():
    data = request.get_json()

    if not data:
        # handle form submission
        site     = request.form.get("site")
        email    = request.form.get("email", current_user.email)
        query    = request.form.get("query", None)
        schedule = request.form.get("schedule", None)
    else:
        site     = data.get("site")
        email    = data.get("email", current_user.email)
        query    = data.get("query", None)
        schedule = data.get("schedule", None)

    if not site:
        flash("Please enter a website.", "error")
        return redirect(url_for("main.home"))

    # create job
    job = Job(
        site=site,
        email=email,
        query=query,
        schedule=schedule,
        status=JobStatus.running,
        user_id=current_user.id
    )
    db.session.add(job)
    db.session.commit()

    try:
        print(f"Resolving site: {site}")
        url = resolve_site(site)
        job.result_url = url
        db.session.commit()
        print(f"Resolved to: {url}")

        print(f"Scraping: {url}")
        result = fetch_page(url)

        if not result["success"]:
            raise Exception(f"Failed to fetch page: {result.get('error')}")

        print("Summarising with Groq...")
        summary = summarise_content(site, result["text"], query)

        print(f"Sending email to {email}...")
        send_report_email(email, site, summary)

        job.status = JobStatus.done
        job.last_run_at = datetime.utcnow()
        db.session.commit()

        flash(f"Report sent to {email} successfully!", "success")
        return redirect(url_for("main.jobs"))

    except Exception as e:
        job.status = JobStatus.failed
        job.error_msg = str(e)
        db.session.commit()
        flash(f"Scrape failed: {str(e)}", "error")
        return redirect(url_for("main.home"))


@main.route("/health")
def health():
    return jsonify({"status": "healthy"})