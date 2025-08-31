from cedarpy import AuthzResult


class BaseSharingError(Exception):
    """Base class for sharing-related errors."""

    pass


class ResourceNotFoundError(BaseSharingError):
    """Error raised when a resource cannot be found."""

    pass


class AuthorisationError(BaseSharingError):
    """Error raised when a user is not authorised to perform an action."""

    def __init__(self, message: str, detail: AuthzResult):
        super().__init__(message)
        self.detail = detail
