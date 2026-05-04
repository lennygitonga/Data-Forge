from app import create_app, db
from app.scheduler import start_scheduler
import os

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Database tables created")

    start_scheduler(app)

    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    app.run(debug=debug, use_reloader=False, host="0.0.0.0", port=port)