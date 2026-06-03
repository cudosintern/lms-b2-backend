import os
from dotenv import load_dotenv
from datetime import timedelta
from slowapi import Limiter
import logging

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

# Load environment variables from .env file
load_dotenv(override=True)


class Settings:
    ENV = os.getenv("ENV", "development")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        30
    ))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    SESSION_EXPIRY_MINUTES = int(os.getenv("SESSION_EXPIRY_MINUTES", 60))
    INACTIVITY_EXPIRY_MINUTES = int(os.getenv(
        "INACTIVITY_EXPIRY_MINUTES",
        120
    ))
    MAX_SESSIONS = int(os.getenv("MAX_SESSIONS", 3))
    # Lock the account after 5 failed attempts
    MAX_FAILED_ATTEMPTS = 5
    # Auto-unlock after 15 minutes
    LOCKOUT_DURATION = timedelta(minutes=15)

    # OAuth2 Credentials
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

    # Backend URL
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Rate Limiting Configuration
    # Max attempts
    RATELIMIT_ENABLED = os.getenv(
        "RATELIMIT_ENABLED", "True"
    ).lower() in ("true", "1", "t")
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 600))
    # Time window in seconds
    RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 360))
    limiter = Limiter(
        key_func=lambda request: request.client.host,
        application_limits=[
            f"{RATE_LIMIT_REQUESTS} per {RATE_LIMIT_WINDOW} seconds"
        ],
        # default_limits=[
        #     f"{RATE_LIMIT_REQUESTS} per {RATE_LIMIT_WINDOW} seconds"
        # ]
    )

    # Debugging: Print environment variables
    def __init__(self):
        logger.info(f"ENVIRONMENT: {self.ENV}")
        logger.info(f"DEBUG: {self.DEBUG}")
        logger.info(f"RATELIMIT_ENABLED: {self.RATELIMIT_ENABLED}")
        if self.RATELIMIT_ENABLED:
            logger.info(f"RATE_LIMIT_REQUESTS: {self.RATE_LIMIT_REQUESTS}")
            logger.info(f"RATE_LIMIT_WINDOW: {self.RATE_LIMIT_WINDOW}")


settings = Settings()
limiter = settings.limiter
