from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.scraper import fetch_page
from app.ai import resolve_site, summarise_content
from app.emailer import send_report_email, send_error_email
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
    jobs = Job.query.filter(Job.user_id == current_user.id)\
               .order_by(Job.created_at.desc()).limit(5).all()
    return render_template("dashboard/home.html", jobs=jobs)


@main.route("/jobs")
@login_required
def jobs():
    all_jobs = Job.query.filter(Job.user_id == current_user.id)\
                  .order_by(Job.created_at.desc()).all()
    return render_template("dashboard/jobs.html", jobs=all_jobs)


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
        site       = request.form.get("site")
        email      = request.form.get("email", current_user.email)
        user_query = request.form.get("user_query", None)
        schedule   = request.form.get("schedule", None)
    else:
        site       = data.get("site")
        email      = data.get("email", current_user.email)
        user_query = data.get("user_query", None)
        schedule   = data.get("schedule", None)

    if not site:
        flash("Please enter a website.", "error")
        return redirect(url_for("main.home"))

    job = Job(
        site=site,
        email=email,
        user_query=user_query,
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
        summary = summarise_content(site, result["text"], user_query)

        print(f"Sending email to {email}...")
        send_report_email(email, site, summary)

        job.status = JobStatus.done
        job.last_run_at = datetime.utcnow()
        db.session.commit()

        if schedule:
            from app.scheduler import schedule_job
            schedule_job(current_app._get_current_object(), job)

        flash(f"Report sent to {email} successfully!", "success")
        return redirect(url_for("main.jobs"))

    except Exception as e:
        job.status = JobStatus.failed
        job.error_msg = str(e)
        db.session.commit()
        send_error_email(email, site, str(e))
        flash(f"Scrape failed: {str(e)}", "error")
        return redirect(url_for("main.home"))


@main.route("/health")
def health():
    return jsonify({"status": "healthy"})


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Message sent! We will get back to you soon.", "success")
        return redirect(url_for("main.contact"))
    return render_template("contact.html")


# ─── API ENDPOINTS FOR CLI ────────────────────────────────────────────────────

@main.route("/api/scrape", methods=["POST"])
def api_scrape():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    site       = data.get("site")
    email      = data.get("email")
    user_query = data.get("user_query", None)
    schedule   = data.get("schedule", None)

    if not site:
        return jsonify({"error": "site is required"}), 400
    if not email:
        return jsonify({"error": "email is required"}), 400

    job = Job(
        site=site,
        email=email,
        user_query=user_query,
        schedule=schedule,
        status=JobStatus.running
    )
    db.session.add(job)
    db.session.commit()

    try:
        print(f"Resolving site: {site}")
        url = resolve_site(site)
        job.result_url = url
        db.session.commit()

        print(f"Scraping: {url}")
        result = fetch_page(url)

        if not result["success"]:
            raise Exception(f"Failed to fetch: {result.get('error')}")

        print("Summarising with Groq...")
        summary = summarise_content(site, result["text"], user_query)

        print(f"Sending email to {email}...")
        send_report_email(email, site, summary)

        job.status = JobStatus.done
        job.last_run_at = datetime.utcnow()
        db.session.commit()

        if schedule:
            from app.scheduler import schedule_job
            schedule_job(current_app._get_current_object(), job)

        return jsonify({
            "success": True,
            "job_id": job.id,
            "url": url,
            "message": f"Report sent to {email}"
        })

    except Exception as e:
        job.status = JobStatus.failed
        job.error_msg = str(e)
        db.session.commit()
        send_error_email(email, site, str(e))
        return jsonify({"error": str(e)}), 500


@main.route("/api/jobs", methods=["GET"])
def api_jobs():
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return jsonify([
        {
            "id": job.id,
            "site": job.site,
            "email": job.email,
            "status": job.status.value,
            "schedule": job.schedule,
            "url": job.result_url,
            "created_at": job.created_at.isoformat(),
            "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None
        }
        for job in jobs
    ])


@main.route("/api/jobs/<int:job_id>", methods=["DELETE"])
def api_delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return jsonify({"success": True, "message": f"Job {job_id} deleted"})