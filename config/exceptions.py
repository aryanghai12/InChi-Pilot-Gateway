import uuid
from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
    NotFound,
    MethodNotAllowed,
)
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Standardized DRF Exception Handler.
    Enforces the response shape:
    {
        "code": "string",
        "message": "string",
        "field_errors": { "field_name": ["error"] },
        "correlation_id": "uuid"
    }

    Specific error code mappings:
    - NotAuthenticated -> 401 with code "not_authenticated"
    - PermissionDenied -> 403 with code "permission_denied"
    - ValidationError  -> 400 with code "validation_error"
    """
    # Call DRF's default exception handler first to get the standard response
    response = exception_handler(exc, context)

    # Get correlation_id from request if available
    request = context.get("request")
    correlation_id = getattr(request, "correlation_id", str(uuid.uuid4()))

    if response is None:
        # Unhandled 500 server error
        return Response(
            {
                "code": "internal_error",
                "message": "An unexpected server error occurred. Please contact support.",
                "field_errors": {},
                "correlation_id": correlation_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Determine standard code and message
    error_code = "error"
    message = "An error occurred."
    field_errors = {}

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        error_code = "not_authenticated"
        message = "Authentication credentials were not provided or are invalid."
        response.status_code = status.HTTP_401_UNAUTHORIZED

    elif isinstance(exc, PermissionDenied):
        error_code = "permission_denied"
        message = getattr(exc, "detail", "You do not have permission to perform this action.")
        response.status_code = status.HTTP_403_FORBIDDEN

    elif isinstance(exc, ValidationError):
        error_code = "validation_error"
        message = "Input validation failed. Please check field errors."
        response.status_code = status.HTTP_400_BAD_REQUEST

        if isinstance(response.data, dict):
            for key, val in response.data.items():
                if isinstance(val, list):
                    field_errors[key] = [str(item) for item in val]
                else:
                    field_errors[key] = [str(val)]
        elif isinstance(response.data, list):
            field_errors["non_field_errors"] = [str(item) for item in response.data]

    elif isinstance(exc, NotFound):
        error_code = "not_found"
        message = getattr(exc, "detail", "The requested resource was not found.")
        response.status_code = status.HTTP_404_NOT_FOUND

    elif isinstance(exc, MethodNotAllowed):
        error_code = "method_not_allowed"
        message = getattr(exc, "detail", f"Method '{request.method}' not allowed.")
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED

    else:
        # Default fallback
        if isinstance(response.data, dict) and "detail" in response.data:
            message = str(response.data["detail"])
        elif isinstance(response.data, str):
            message = response.data

    response.data = {
        "code": error_code,
        "message": str(message),
        "field_errors": field_errors,
        "correlation_id": correlation_id,
    }

    return response
