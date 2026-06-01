from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import status, Request
from typing import Any, Dict, Optional, Union
import logging

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


class ResponseUtils:
    @staticmethod
    def _add_cors_headers(
        response: JSONResponse,
        request: Optional[Request] = None,
        origin: Optional[str] = None
    ) -> JSONResponse:
        """Internal method to add CORS headers"""
        cors_origin = origin or (
            request.headers.get("origin", "*") if request else "*"
        )
        response.headers.update({
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        })
        return response

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None,
        *,
        request: Optional[Request] = None,
        cors: bool = True,
        cors_origin: Optional[str] = None
    ) -> JSONResponse:
        """Standard success response format"""
        serializable_data = jsonable_encoder(data)
        content = {
            "status": True,
            "message": message,
            "data": serializable_data
        }
        response = JSONResponse(
            content=content,
            status_code=status_code,
            headers=headers or {}
        )
        return ResponseUtils._add_cors_headers(
            response, request, cors_origin
        ) if cors else response

    @staticmethod
    def error(
        message: str = "An error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_details: Optional[Union[str, Dict]] = None,
        error_code: Optional[Union[str, int]] = None,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        *,
        request: Optional[Request] = None,
        cors: bool = True,
        cors_origin: Optional[str] = None
    ) -> JSONResponse:
        """Standard error response format"""
        serializable_error_details = jsonable_encoder(error_details or message)
        error_response_data = {
            "message": message,
            "details": serializable_error_details,
        }
        if error_code is not None:
            error_response_data["code"] = error_code
        if error_type is not None:
            error_response_data["type"] = error_type
        if stack_trace is not None:
            error_response_data["stack_trace"] = stack_trace

        content = {
            "status": False,
            "message": message,
            "error": error_response_data
        }
        logger.error(
            f"API Error: {message} | Status: {status_code}|Details: "
            f"{serializable_error_details}"
        )
        response = JSONResponse(
            content=content,
            status_code=status_code,
            headers=headers or {}
        )
        return ResponseUtils._add_cors_headers(
            response, request, cors_origin
        ) if cors else response

    @staticmethod
    def paginated(
        data: Any,
        total: int,
        page: int,
        limit: int,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
        headers: Optional[Dict[str, str]] = None,
        *,
        request: Optional[Request] = None,
        cors: bool = True,
        cors_origin: Optional[str] = None
    ) -> JSONResponse:
        """Standard paginated response format"""
        # Use jsonable_encoder for paginated data as well
        serializable_data = jsonable_encoder(data)
        content = {
            "status": True,
            "message": message,
            "data": serializable_data,
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit
            }
        }
        response = JSONResponse(
            content=content,
            status_code=status_code,
            headers=headers or {}
        )
        return ResponseUtils._add_cors_headers(
            response, request, cors_origin
        ) if cors else response

    @staticmethod
    def with_cors(
        response: JSONResponse, request: Request, origin: Optional[str] = None
    ) -> JSONResponse:
        """Explicit CORS header addition for any response"""
        return ResponseUtils._add_cors_headers(response, request, origin)
