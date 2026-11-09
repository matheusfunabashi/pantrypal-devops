import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Writes one stdout line per HTTP request: method, path, status, duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "method=%s path=%s status=%s duration_ms=%.0f",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
