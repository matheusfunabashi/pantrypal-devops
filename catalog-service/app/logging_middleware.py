import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("request")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Writes one stdout line per HTTP request: method, path, status, duration."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        status_code = 500  # a handler that raises is logged as a 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "method=%s path=%s status=%s duration_ms=%.0f",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )
