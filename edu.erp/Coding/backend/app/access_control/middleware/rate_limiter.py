from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
# from slowapi.middleware import SlowAPIASGIMiddleware
from fastapi import Request
from starlette.responses import JSONResponse
from ..config.settings import settings


class RateLimiter():
    # Custom exception handler for rate limiting
    @staticmethod
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Please try again later."}
        )

    @classmethod
    def register(cls, app):
        # Set the rate limiter from settings
        app.state.limiter = settings.limiter

        # Register the custom exception handler
        app.add_exception_handler(RateLimitExceeded, cls.rate_limit_handler)

        # Add the rate-limiting middleware
        app.add_middleware(SlowAPIMiddleware)
        # SlowAPIASGIMiddleware works better but currently has issues
        # will be used later if the issues are resolved
        # app.add_middleware(SlowAPIASGIMiddleware)
