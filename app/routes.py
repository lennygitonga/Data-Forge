from flask import Blueprint, jsonify, request
from app.scraper import fetch_page
from app.ai import resolve_site, summarise_content
from app.emailer import send_report_email
from app import db
from app.models import Job, JobStatus
from datetime import datetime

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return jsonify({"status": "ok", "message": "Data-Forge is running"})


@main.route("/health")
def health():
    return jsonify({"status": "healthy"})


@main.route("/scrape", methods=["POST"])
def scrape():
    """
    Main endpoint — receives a site name and email,
    scrapes the site, summarises with AI, sends email.
    """
    data = request.get_json()

    # validate inputs
    if not data:
        return jsonify({"error": "No data provided"}), 400

    site = data.get("site")
    email = data.get("email")
    query = data.get("query", None)

    if not site:
        return jsonify({"error": "site is required"}), 400
    if not email:
        return jsonify({"error": "email is required"}), 400

    # create a job record in the database
    job = Job(
        site=site,
        email=email,
        query=query,
        status=JobStatus.running
    )
    db.session.add(job)
    db.session.commit()

    try:
        # step 1 — resolve the site name to a URL
        print(f"Resolving site: {site}")
        url = resolve_site(site)
        job.result_url = url
        db.session.commit()
        print(f"Resolved to: {url}")

        # step 2 — scrape the page
        print(f"Scraping: {url}")
        result = fetch_page(url)

        if not result["success"]:
            raise Exception(f"Failed to fetch page: {result.get('error')}")

        # step 3 — summarise with Gemini
        print("Summarising with Groq...")
        summary = summarise_content(site, result["text"], query)

        # step 4 — send email
        print(f"Sending email to {email}...")
        send_report_email(email, site, summary)

        # mark job as done
        job.status = JobStatus.done
        job.last_run_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "success": True,
            "job_id": job.id,
            "url": url,
            "message": f"Report sent to {email}"
        })

    except Exception as e:
        # mark job as failed
        job.status = JobStatus.failed
        job.error_msg = str(e)
        db.session.commit()
        print(f"Job failed: {e}")
        return jsonify({"error": str(e)}), 500


@main.route("/jobs", methods=["GET"])
def get_jobs():
    """
    Returns all scrape jobs.
    """
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return jsonify([
        {
            "id": job.id,
            "site": job.site,
            "email": job.email,
            "status": job.status.value,
            "url": job.result_url,
            "created_at": job.created_at.isoformat(),
            "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None
        }
        for job in jobs
    ])