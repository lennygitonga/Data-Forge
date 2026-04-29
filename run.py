from app import create_app, db
from app.scheduler import start_scheduler

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✓ Database tables created")

    start_scheduler(app)

    app.run(debug=True, use_reloader=False)