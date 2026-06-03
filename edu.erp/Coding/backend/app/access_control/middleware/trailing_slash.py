from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse


class NormalizeTrailingSlashMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, strip_trailing_slash: bool = True):
        super().__init__(app)
        self.strip = strip_trailing_slash

    async def dispatch(self, request: Request, call_next):
        path = request.scope["path"]

        # Don't touch the root
        if path == "/":
            return await call_next(request)

        if self.strip and path.endswith("/"):
            # Redirect /path/ → /path
            new_path = path.rstrip("/")
            if request.url.path != new_path:
                return RedirectResponse(
                    url=str(request.url.replace(path=new_path))
                )
        elif not self.strip and not path.endswith("/"):
            # Redirect /path → /path/
            new_path = path + "/"
            if request.url.path != new_path:
                return RedirectResponse(
                    url=str(request.url.replace(path=new_path))
                )

        return await call_next(request)
