from typing import Any, Dict, Optional

class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        code: str = "INTERNAL_ERROR",
        details: Optional[Any] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(self.message)

class EntityNotFoundException(AppException):
    """Raised when a requested resource is not found."""
    def __init__(self, message: str = "Resource not found", details: Optional[Any] = None):
        super().__init__(message, status_code=404, code="NOT_FOUND", details=details)

class BusinessLogicException(AppException):
    """Raised when a business rule is violated."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, status_code=422, code="BUSINESS_RULE_VIOLATION", details=details)

class UnauthorizedException(AppException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Unauthorized", details: Optional[Any] = None):
        super().__init__(message, status_code=401, code="UNAUTHORIZED", details=details)

class ForbiddenException(AppException):
    """Raised when a user lacks permission."""
    def __init__(self, message: str = "Forbidden", details: Optional[Any] = None):
        super().__init__(message, status_code=403, code="FORBIDDEN", details=details)

class ResourceConflictException(AppException):
    """Raised when a resource already exists or there's a conflict."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, status_code=409, code="CONFLICT", details=details)

class ResourceGoneException(AppException):
    """Raised when a resource is no longer available (e.g., product out of stock)."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message, status_code=410, code="GONE", details=details)
