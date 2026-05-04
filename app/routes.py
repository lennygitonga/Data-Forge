from flask import Blueprint, jsonify, request, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, logout_user
from app.scraper import fetch_page
from app.ai import resolve_site, summarise_content
from app.emailer import send_report_email, send_error_email
from app import db, bcrypt
from app.models import Job, JobStatus, User
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


@main.route("/jobs/<int:job_id>/cancel", methods=["POST"])
@login_required
def cancel_job(job_id):
    job = Job.query.get_or_404(job_id)

    try:
        from app.scheduler import scheduler
        scheduler.remove_job(f"job_{job_id}")
        print(f"Scheduler job {job_id} cancelled")
    except Exception as e:
        print(f"Could not remove from scheduler: {e}")

    job.schedule = None
    job.status = JobStatus.done
    db.session.commit()

    flash("Scheduled job cancelled.", "success")
    return redirect(url_for("main.jobs"))


@main.route("/settings")
@login_required
def settings():
    return render_template("settings.html")


@main.route("/settings/profile", methods=["POST"])
@login_required
def update_profile():
    name  = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()

    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("main.settings"))

    existing = User.query.filter_by(email=email).first()
    if existing and existing.id != current_user.id:
        flash("That email is already in use by another account.", "error")
        return redirect(url_for("main.settings"))

    current_user.name  = name
    current_user.email = email
    db.session.commit()

    flash("Profile updated successfully.", "success")
    return redirect(url_for("main.settings"))


@main.route("/settings/password", methods=["POST"])
@login_required
def update_password():
    current_pw = request.form.get("current_password", "")
    new_pw     = request.form.get("new_password", "")
    confirm_pw = request.form.get("confirm_password", "")

    if not current_pw or not new_pw or not confirm_pw:
        flash("All password fields are required.", "error")
        return redirect(url_for("main.settings") + "?tab=password")

    if not bcrypt.check_password_hash(current_user.password, current_pw):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("main.settings") + "?tab=password")

    if new_pw != confirm_pw:
        flash("New passwords do not match.", "error")
        return redirect(url_for("main.settings") + "?tab=password")

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for("main.settings") + "?tab=password")

    current_user.password = bcrypt.generate_password_hash(new_pw).decode("utf-8")
    db.session.commit()

    flash("Password updated successfully.", "success")
    return redirect(url_for("main.settings"))


@main.route("/settings/delete-jobs", methods=["POST"])
@login_required
def delete_all_jobs():
    jobs = Job.query.filter(Job.user_id == current_user.id).all()

    from app.scheduler import scheduler
    for job in jobs:
        try:
            scheduler.remove_job(f"job_{job.id}")
        except Exception:
            pass

    Job.query.filter(Job.user_id == current_user.id).delete()
    db.session.commit()

    flash("All jobs deleted successfully.", "success")
    return redirect(url_for("main.settings") + "?tab=danger")


@main.route("/settings/delete-account", methods=["POST"])
@login_required
def delete_account():
    from app.scheduler import scheduler

    jobs = Job.query.filter(Job.user_id == current_user.id).all()
    for job in jobs:
        try:
            scheduler.remove_job(f"job_{job.id}")
        except Exception:
            pass

    Job.query.filter(Job.user_id == current_user.id).delete()

    user = current_user._get_current_object()
    logout_user()
    db.session.delete(user)
    db.session.commit()

    flash("Your account has been deleted.", "success")
    return redirect(url_for("auth.login"))


@main.route("/scrape", methods=["POST"])
@login_required
def scrape():
    if request.content_type and "application/json" in request.content_type:
        data       = request.get_json()
        site       = data.get("site")
        email      = data.get("email", current_user.email)
        user_query = data.get("user_query", None)
        schedule   = data.get("schedule", None)
    else:
        site       = request.form.get("site")
        email      = request.form.get("email", current_user.email)
        user_query = request.form.get("user_query", None)
        schedule   = request.form.get("schedule", None)

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