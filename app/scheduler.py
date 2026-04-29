from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.scraper import fetch_page
from app.ai import resolve_site, summarise_content
from app.emailer import send_report_email
from datetime import datetime

scheduler = BackgroundScheduler()


def run_job(app, job_id):
    """Runs a single scrape job inside the app context."""
    with app.app_context():
        from app import db
        from app.models import Job, JobStatus

        job = Job.query.get(job_id)
        if not job:
            return

        job.status = JobStatus.running
        db.session.commit()

        try:
            url = resolve_site(job.site)
            job.result_url = url
            db.session.commit()

            result = fetch_page(url)
            if not result["success"]:
                raise Exception(f"Fetch failed: {result.get('error')}")

            summary = summarise_content(job.site, result["text"], job.user_query)
            send_report_email(job.email, job.site, summary)

            job.status = JobStatus.done
            job.last_run_at = datetime.utcnow()
            db.session.commit()
            print(f"✓ Scheduled job {job_id} completed")

        except Exception as e:
            job.status = JobStatus.failed
            job.error_msg = str(e)
            db.session.commit()
            print(f"✗ Scheduled job {job_id} failed: {e}")


def schedule_job(app, job):
    """Parses the schedule string and adds job to APScheduler."""
    schedule = job.schedule
    if not schedule:
        return

    # parse "every 1h", "every 6h", "every 24h", "every 7d"
    try:
        parts = schedule.lower().replace("every ", "").strip()
        if parts.endswith("h"):
            hours = int(parts[:-1])
            trigger = IntervalTrigger(hours=hours)
        elif parts.endswith("d"):
            days = int(parts[:-1])
            trigger = IntervalTrigger(days=days)
        else:
            print(f"Unknown schedule format: {schedule}")
            return

        scheduler.add_job(
            func=run_job,
            trigger=trigger,
            args=[app, job.id],
            id=f"job_{job.id}",
            replace_existing=True
        )
        print(f"✓ Scheduled job {job.id} — {schedule}")

    except Exception as e:
        print(f"✗ Failed to schedule job {job.id}: {e}")


def start_scheduler(app):
    """Starts APScheduler and loads all existing scheduled jobs."""
    with app.app_context():
        from app.models import Job, JobStatus

        scheduler.start()
        print("✓ Scheduler started")

        # load existing scheduled jobs from database
        jobs = Job.query.filter(
            Job.schedule.isnot(None)
        ).all()

        for job in jobs:
            schedule_job(app, job)
            print(f"  Loaded scheduled job: {job.site} — {job.schedule}")