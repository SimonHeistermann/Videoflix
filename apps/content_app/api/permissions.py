"""
Custom permission classes for the content application.
"""

from rest_framework.permissions import BasePermission


class IsAuthenticatedAndActive(BasePermission):
    """
    Permission that grants access only to authenticated and active users.

    Note:
        This permission is optional. If you only need authentication without
        checking the user's active status, you can use DRF's built-in
        `IsAuthenticated` permission directly in your views.
    """

    def has_permission(self, request, view):
        """
        Determine whether the request should be permitted.

        Args:
            request: The incoming HTTP request.
            view: The view being accessed.

        Returns:
            bool: True if the user is authenticated and active, otherwise False.
        """
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "is_active", False))