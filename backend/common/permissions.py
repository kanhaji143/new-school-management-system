"""DRF permission classes used across the API."""
from rest_framework import permissions


class IsAuthenticatedInInstitution(permissions.BasePermission):
    """Ensures the user belongs to the request's institution."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and getattr(user, "institution_id", None))


class HasRole(permissions.BasePermission):
    """Allow only users holding one of the given roles in the current institution."""

    def __init__(self, *roles):
        self.roles = roles
        super().__init__()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.has_any_role(*self.roles)


# Convenience role-based classes -------------------------------------------------
class IsAdmin(HasRole):
    def __init__(self):
        super().__init__("SCHOOL_ADMIN", "SUPER_ADMIN")


class IsCoordinator(HasRole):
    def __init__(self):
        super().__init__("COORDINATOR", "SCHOOL_ADMIN", "SUPER_ADMIN")


class IsTeacher(HasRole):
    def __init__(self):
        super().__init__("TEACHER")


class IsParent(HasRole):
    def __init__(self):
        super().__init__("PARENT")


class IsStudent(HasRole):
    def __init__(self):
        super().__init__("STUDENT")


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
