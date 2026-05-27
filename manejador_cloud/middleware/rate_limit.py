
import logging
import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

_PROTECTED: set[tuple[str, str]] = {("POST", "/projects")}


def _client_ip(request: Request) -> str:
   
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):


    def __init__(self, app, redis_client):
        super().__init__(app)
        self.redis = redis_client

    async def dispatch(self, request: Request, call_next):
        
        enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        if not enabled:
            return await call_next(request)

        method = request.method
        path = request.url.path.rstrip("/") or "/"

        if (method, path) not in _PROTECTED:
            return await call_next(request)

        limit  = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
        window = int(os.getenv("RATE_LIMIT_WINDOW",   "10"))
        ip     = _client_ip(request)
        key    = f"rl:{ip}:{method}:{path}"

        try:
            count = self.redis.incr(key)
            
            if count == 1:
                self.redis.expire(key, window)
        except Exception as exc:
            logger.warning("RateLimitMiddleware: Redis error — failing open: %s", exc)
            return await call_next(request)

        if count > limit:
            logger.warning(
                "Rate limit exceeded | ip=%s count=%d limit=%d window=%ds",
                ip, count, limit, window,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        f"Rate limit exceeded. "
                        f"Max {limit} POST /projects requests per {window} s. "
                        f"Retry after {window} s."
                    )
                },
                headers={"Retry-After": str(window)},
            )

        return await call_next(request)
