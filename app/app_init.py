import logging
import sys
import time

import aioredis
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.backends.redis import RedisBackend
from loguru import logger
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette import status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.v1.api import api_router
from app.config import settings


def configure_logger():
    """Configure logger to contain request ID and endpoint relevant details"""
    logger_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<magenta>{extra[request_id]}</magenta> | "
        "<blue>{extra[path]}</blue> | "
        "<level>{message}</level> |"
        "<cyan>{extra}</cyan>"
    )
    logger.configure(extra={"request_id": "", "path": ""})  # Default values
    logger.remove()
    logger.add(
        sys.stdout,
        format=logger_format,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )


def rate_limit_response_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return custom response when rate limit exceeded.

    Args:
        request: Incoming request
        exc: Raised rate limit exception

    Returns:
        Resp. to be return to the client
    """
    response = JSONResponse(
        {"detail": f"Rate limit exceeded: {exc.detail}"},
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    )
    response = request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
    return response


def get_rate_limit() -> str:
    """Use limits as a callable, so we can change it during tests"""
    return settings.RATE_LIMIT


def get_rate_limit_cache_key(request: Request) -> str:
    """
    Determine the cache key for rate limiter
    """
    if auth := request.headers.get("Authorization"):
        return auth

    return request.client.host or "127.0.0.1"


class RequestMiddleware(BaseHTTPMiddleware):
    """Log requests, handle unexpected error and add request ID to logger with context manager"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        with logger.contextualize(
            request_id=correlation_id.get(),
            user_agent=request.headers.get("User-Agent"),
            path=request.scope["path"],
        ):
            logger.info(f"request.start")
            start_time = time.time()

            try:
                response = await call_next(request)
            except Exception as e:
                # Other exceptions are handled before it comes here and proper response is returned
                logger.exception(f"request.internal_error",)
                response = JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Internal error"},
                )

            # Log process time and add it to the response header
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            logger.info(
                f"request.end",
                process_time=process_time,
                status_code=response.status_code,
            )
            return response


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )
    # Configure exception handlers
    app.add_exception_handler(RateLimitExceeded, rate_limit_response_handler)

    # Configure middlewares
    app.add_middleware(SlowAPIMiddleware)  # Rate limits
    app.add_middleware(RequestMiddleware)  # Log request with its id
    app.add_middleware(
        CorrelationIdMiddleware
    )  # Add correlation (request) id to context

    # Configure routes
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    # Set global rate limit settings
    # NOTE: If REDIS_URI is empty, in-memory cache will be used
    app.state.limiter = Limiter(
        key_func=get_rate_limit_cache_key,
        default_limits=[get_rate_limit],
        storage_uri=settings.REDIS_URI if settings.REDIS_URI else None,
    )

    # Initialize API caching
    # NOTE: If REDIS_URI is empty, in-memory cache will be used
    cache_backend = InMemoryBackend()
    if settings.REDIS_URI:
        cache_backend = RedisBackend(
            aioredis.from_url(
                settings.REDIS_URI, encoding="utf8", decode_responses=True
            )
        )

    FastAPICache.init(cache_backend)

    # Configure logger with its styles
    configure_logger()

    logger.info("App initiated")
    return app
