import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-this")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    # required for flask-dance on http in development
    OAUTHLIB_INSECURE_TRANSPORT = "1"

    SQLALCHEMY_ENGINE_OPTIONS = {
    "connect_args": {"sslmode": "require"}
}