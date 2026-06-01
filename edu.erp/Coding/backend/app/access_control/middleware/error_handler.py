from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymysql.err import (
    MySQLError, OperationalError, ProgrammingError, IntegrityError, DataError,
    InternalError, NotSupportedError
)
from sqlalchemy.exc import SQLAlchemyError
import traceback
import logging
from typing import Any, Dict, Optional, Tuple, Type
import sys
from app.access_control.utils.response_utils import ResponseUtils
from app.access_control.config.settings import settings

# Configure Logging
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


class ExceptionHandler():
    @staticmethod
    def _get_error_details(
        exc: Exception,
        exc_info: Optional[
            Tuple[Type[BaseException], BaseException, Any]
        ] = None
    ) -> Dict[str, Any]:
        # Use provided exc_info or get current if not provided
        if exc_info is None:
            exc_info = sys.exc_info()

        stack_trace = None
        if settings.DEBUG:
            # Try to get the traceback from the current exception context first
            if exc_info and exc_info[0] is not None:
                stack_trace = "".join(traceback.format_exception(*exc_info))
            else:
                # Fallback to traceback.format_exc() which gets the traceback
                # of the last exception that occurred,
                # regardless of current frame
                formatted_exc = traceback.format_exc()
                # Check if format_exc returned a meaningful traceback
                # or just a generic one
                if "NoneType: None" not in formatted_exc and \
                        "Traceback (most recent call last):" in formatted_exc:
                    stack_trace = formatted_exc

        details = {
            "status_code": getattr(exc, "status_code", 500),
            "detail": str(exc),
            "type": exc.__class__.__name__,
            "stack_trace": stack_trace,
            "error_code": getattr(exc, "code", None)
        }

        # Special handling for HTTPException
        # to get the correct status code and detail
        if isinstance(exc, HTTPException):
            details["status_code"] = exc.status_code
            details["detail"] = exc.detail

        # Special handling for database errors to extract error code from args
        if isinstance(exc, (MySQLError, SQLAlchemyError)) and \
           hasattr(exc, "args") and exc.args:
            try:
                # Attempt to extract integer error code from the first argument
                if isinstance(exc.args[0], int):
                    details["error_code"] = exc.args[0]
                elif isinstance(exc.args[0], str) and exc.args[0].isdigit():
                    details["error_code"] = int(exc.args[0])
                # If the first arg is not a digit, check if it\"s a tuple/list
                # with a digit
                elif isinstance(exc.args[0], (tuple, list)) and \
                        len(exc.args[0]) > 0 and str(exc.args[0][0]).isdigit():
                    details["error_code"] = int(exc.args[0][0])
            except (ValueError, TypeError):
                details["error_code"] = None

            # For database errors, the detail might be in the second argument
            # or a specific attribute
            if len(exc.args) > 1 and isinstance(exc.args[1], str):
                details["detail"] = exc.args[1]
            elif hasattr(exc, "orig") and hasattr(exc.orig, "args") and \
                    exc.orig.args and len(exc.orig.args) > 1 and \
                    isinstance(exc.orig.args[1], str):
                details["detail"] = exc.orig.args[1]

        return details

    @staticmethod
    async def http_exception_handler(request: Request, exc: HTTPException):
        error_details = ExceptionHandler._get_error_details(
            exc, sys.exc_info()
        )
        # logger.warning(f"HTTP Exception: {error_details}")
        return ResponseUtils.with_cors(
            ResponseUtils.error(
                message=error_details["detail"],
                status_code=error_details["status_code"],
                error_code=error_details["error_code"],
                error_type=error_details["type"],
                stack_trace=error_details["stack_trace"]
            ),
            request
        )

    @staticmethod
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Capture exc_info here, where the exception context is still fresh
        current_exc_info = sys.exc_info()
        error_details = ExceptionHandler._get_error_details(
            exc, current_exc_info
        )
        # logger.error(
        #     f"Unexpected error: {error_details["type"]}: "
        #     f"{error_details["detail"]}\n{error_details["stack_trace"]}",
        #     extra={
        #         "path": request.url.path,
        #         "method": request.method,
        #         "error_type": error_details["type"],
        #         "stack_trace": error_details["stack_trace"]
        #     }
        # )
        return ResponseUtils.with_cors(
            ResponseUtils.error(
                message=error_details["detail"],
                status_code=error_details["status_code"],
                error_code=error_details["error_code"],
                error_type=error_details["type"],
                stack_trace=error_details["stack_trace"]
            ),
            request
        )

    @staticmethod
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        error_details = ExceptionHandler._get_error_details(
            exc, sys.exc_info()
        )
        formatted_errors = [
            {
                "field": "->".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            }
            for error in exc.errors()
        ]

        # logger.warning(
        #     "Request validation failed",
        #     extra={
        #         "path": request.url.path,
        #         "method": request.method,
        #         "errors": error_details,
        #         # "body": await request.body()
        #     }
        # )

        return ResponseUtils.with_cors(
            ResponseUtils.error(
                message="Invalid request data",
                status_code=error_details["status_code"],
                error_code=error_details["error_code"],
                error_type=error_details["type"],
                stack_trace=error_details["stack_trace"],
                error_details={"errors": formatted_errors}
            ),
            request
        )

    @staticmethod
    async def database_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        error_details = ExceptionHandler._get_error_details(
            exc, sys.exc_info()
        )

        # Categorize the error for proper status code
        status_code = 500  # Default
        if isinstance(exc, OperationalError):
            status_code = 503  # Service Unavailable
        elif isinstance(exc, (ProgrammingError, DataError, NotSupportedError)):
            status_code = 400  # Bad Request
        elif isinstance(exc, IntegrityError):
            status_code = 409  # Conflict
        elif isinstance(exc, InternalError):
            status_code = 500  # Internal Server Error

        # Log the full error details
        # logger.error(
        #     f"Database Error: {error_details["type"]}, "
        #     f"{error_details["error_code"]}, {error_details["detail"]}",
        #     extra={
        #         "path": request.url.path,
        #         "method": request.method,
        #         "error_code": error_details["error_code"],
        #         "error_message": error_details["detail"],
        #         "stack_trace": error_details["stack_trace"]
        #     }
        # )

        # Prepare response - use the original error message directly
        response_data = {
            "message": error_details["detail"],
            "status_code": status_code,
            "error_code": error_details["error_code"],
            "error_type": error_details["type"],
            "stack_trace": error_details["stack_trace"]
        }

        # In production, you might want to use a generic message
        # if not settings.DEBUG:
        #     response_data["error_details"] = {
        #         503: "Database service unavailable",
        #         400: "Invalid database request",
        #         409: "Data conflict occurred",
        #         500: "Database operation failed"
        #     }.get(status_code, "Database error occurred")

        return ResponseUtils.with_cors(
            ResponseUtils.error(**response_data),
            request
        )

    @classmethod
    def register(cls, app) -> None:
        db_errors = [
            MySQLError,
            SQLAlchemyError,
        ]
        for error_type in db_errors:
            app.add_exception_handler(
                error_type, cls.database_exception_handler
            )

        app.add_exception_handler(HTTPException, cls.http_exception_handler)
        app.add_exception_handler(
            RequestValidationError, cls.validation_exception_handler
        )
        app.add_exception_handler(Exception, cls.generic_exception_handler)
