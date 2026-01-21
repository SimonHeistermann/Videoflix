from rest_framework.permissions import BasePermission


class IsAuthenticatedAndActive(BasePermission):
    """
    Optional: If you want to block inactive users from videos.
    If you don't need it, use IsAuthenticated in views.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and getattr(user, "is_active", False))