"""
Utilities for user authentication workflows.

Includes helpers for:
- creating activation/reset links,
- encoding/decoding UID and token,
- cookie naming and cookie configuration,
- setting and deleting auth cookies,
- enqueueing tasks via RQ only after DB commit.
"""

from urllib.parse import quote

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

import django_rq
from rq import Retry

User = get_user_model()

DEFAULT_RETRY = Retry(max=3, interval=[10, 30, 60])


# -----------------------------------------------------------------------------
# RQ helper
# -----------------------------------------------------------------------------
def enqueue_after_commit(task, *args, queue="default", **kwargs):
    """
    Enqueue an RQ job only after the current DB transaction commits.

    This ensures that background tasks (e.g., sending emails) only run after
    the database changes they depend on have been safely committed.

    Args:
        task (callable): Callable to enqueue as an RQ job.
        *args: Positional arguments forwarded to the enqueued task.
        queue (str): RQ queue name.
        **kwargs: Keyword arguments forwarded to the enqueued task.
    """

    def _enqueue():
        django_rq.get_queue(queue).enqueue(
            task,
            *args,
            retry=DEFAULT_RETRY,
            **kwargs,
        )

    transaction.on_commit(_enqueue)


# -----------------------------------------------------------------------------
# Auth helpers
# -----------------------------------------------------------------------------
def register_response(user, token):
    """
    Build the registration response payload.

    Args:
        user (User): The newly created user.
        token (str): A token value to return to the client (e.g., activation token).

    Returns:
        dict: Response payload containing user identity and token.
    """
    return {"user": {"id": user.id, "email": user.email}, "token": token}


def build_uid_and_token(user):
    """
    Build a UID (base64) and token pair for the given user.

    Args:
        user (User): The user instance.

    Returns:
        tuple[str, str]: (uidb64, token) for use in activation/reset flows.
    """
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return uidb64, token


def get_user_from_uid(uidb64):
    """
    Decode a base64 UID and fetch the corresponding user.

    Args:
        uidb64 (str): Base64-encoded user ID.

    Returns:
        User | None: The matching user instance, or None if invalid/not found.
    """
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        return User.objects.get(pk=uid)
    except Exception:
        return None


def try_get_user_by_email(email):
    """
    Try to retrieve a user by email.

    Args:
        email (str): Email address.

    Returns:
        User | None: The matching user instance, or None if not found/invalid.
    """
    if not email:
        return None
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


def build_frontend_link(kind, uidb64, token):
    """
    Build a frontend URL for activation or password reset.

    Args:
        kind (str): Link kind ("activate" or "reset").
        uidb64 (str): Base64 UID.
        token (str): Django token.

    Returns:
        str: Fully qualified frontend link with uid and token query params.
    """
    base = (getattr(settings, "FRONTEND_BASE_URL", "") or "").rstrip("/")
    if not base:
        base = "http://localhost:4200"

    path = frontend_path(kind).lstrip("/")
    return f"{base}/{path}?uid={quote(uidb64)}&token={quote(token)}"


def frontend_path(kind):
    """
    Resolve the frontend path for a given link kind.

    Args:
        kind (str): Link kind ("activate" or "reset").

    Returns:
        str: Relative path for the frontend route/page.
    """
    if kind == "activate":
        return getattr(settings, "FRONTEND_ACTIVATE_PATH", "pages/auth/activate.html")
    if kind == "reset":
        return getattr(settings, "FRONTEND_RESET_PATH", "pages/auth/confirm_password.html")
    return ""


def cookie_name(kind):
    """
    Build the cookie name for access or refresh tokens.

    Respects AUTH_COOKIE_PREFIX.

    Args:
        kind (str): Either "access" or "refresh".

    Returns:
        str: The final cookie key.
    """
    prefix = getattr(settings, "AUTH_COOKIE_PREFIX", "") or ""
    if kind == "access":
        return f"{prefix}access_token"
    return f"{prefix}refresh_token"


def cookie_settings():
    """
    Resolve cookie behavior from settings.

    Uses your chosen setting names:
    - SECURE_COOKIES (bool)
    - JWT_COOKIE_SAMESITE ("Lax"/"Strict"/"None")
    - JWT_COOKIE_DOMAIN (str|None)
    - JWT_COOKIE_PATH (str)

    Returns:
        tuple[bool, str, str | None, str]: (secure, samesite, domain, path)
    """
    secure = getattr(settings, "SECURE_COOKIES", True)
    samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "None")
    domain = getattr(settings, "JWT_COOKIE_DOMAIN", None)
    path = getattr(settings, "JWT_COOKIE_PATH", "/")
    return secure, samesite, domain, path


def set_auth_cookies(response, access, refresh):
    """
    Set both access and refresh cookies on the given response.

    Args:
        response: Django/DRF response object.
        access (str): Access token string.
        refresh (str): Refresh token string.
    """
    set_access_cookie(response, access)
    set_refresh_cookie(response, refresh)


def set_access_cookie(response, access):
    """
    Set the access token cookie on the response.

    Args:
        response: Django/DRF response object.
        access (str): Access token string.
    """
    secure, samesite, domain, path = cookie_settings()
    max_age = int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(
        key=cookie_name("access"),
        value=access,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=max_age,
        domain=domain,
        path=path,
    )


def set_refresh_cookie(response, refresh):
    """
    Set the refresh token cookie on the response.

    Args:
        response: Django/DRF response object.
        refresh (str): Refresh token string.
    """
    secure, samesite, domain, path = cookie_settings()
    max_age = int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds())
    response.set_cookie(
        key=cookie_name("refresh"),
        value=refresh,
        httponly=True,
        secure=secure,
        samesite=samesite,
        max_age=max_age,
        domain=domain,
        path=path,
    )


def delete_auth_cookies(response):
    """
    Delete access and refresh token cookies from the response.

    Args:
        response: Django/DRF response object.
    """
    _, _, domain, path = cookie_settings()
    response.delete_cookie(cookie_name("access"), domain=domain, path=path)
    response.delete_cookie(cookie_name("refresh"), domain=domain, path=path)