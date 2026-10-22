"""Custom DRF exception handler producing the standard error envelope."""
from rest_framework.views import exception_handler


def standard_exception_handler(exc, context):
    from rest_framework.response import Response

    response = exception_handler(exc, context)
    if response is None:
        return None

    if response.status_code == 400 and isinstance(response.data, dict):
        field_errors = {
            key: value if isinstance(value, list) else [str(value)]
            for key, value in response.data.items()
        }
        response.data = {
            "success": False,
            "message": "Validation failed",
            "errors": {"fieldErrors": field_errors, "formErrors": []},
        }
    elif response.status_code == 400:
        # Plain (non-model) serializers raise list-shaped errors.
        data = response.data
        form_errors = [str(item) for item in data] if isinstance(data, list) else [str(data)]
        response.data = {
            "success": False,
            "message": "Validation failed",
            "errors": {"fieldErrors": {}, "formErrors": form_errors},
        }
    else:
        data = response.data
        if isinstance(data, dict):
            message = data.get("detail", "Request failed")
        else:
            message = str(data)
        response.data = {
            "success": False,
            "message": message,
            "errors": {"fieldErrors": {}, "formErrors": [str(message)]},
        }
    return response


class BusinessRuleError(Exception):
    """Raised when a domain invariant is violated."""

    def __init__(self, message, code="business_rule_violation"):
        super().__init__(message)
        self.message = message
        self.code = code
