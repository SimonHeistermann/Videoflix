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
    """
    def _enqueue():
        django_rq.get_queue(queue).enqueue(task, *args, retry=DEFAULT_RETRY, **kwargs)

    transaction.on_commit(_enqueue)


# -----------------------------------------------------------------------------
# Auth helpers
# -----------------------------------------------------------------------------
def register_response(user, token):
    return {"user": {"id": user.id, "email": user.email}, "token": token}


def build_uid_and_token(user):
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    return uidb64, token


def get_user_from_uid(uidb64):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        return User.objects.get(pk=uid)
    except Exception:
        return None


def try_get_user_by_email(email):
    if not email:
        return None
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None


def build_frontend_link(kind, uidb64, token):
    base = (getattr(settings, "FRONTEND_BASE_URL", "") or "").rstrip("/")
    if not base:
        base = "http://localhost:4200"

    path = frontend_path(kind).lstrip("/")
    return f"{base}/{path}?uid={quote(uidb64)}&token={quote(token)}"


def frontend_path(kind):
    if kind == "activate":
        return getattr(settings, "FRONTEND_ACTIVATE_PATH", "pages/auth/activate.html")
    if kind == "reset":
        return getattr(settings, "FRONTEND_RESET_PATH", "pages/auth/confirm_password.html")
    return ""


def cookie_name(kind):
    prefix = getattr(settings, "AUTH_COOKIE_PREFIX", "") or ""
    if kind == "access":
        return f"{prefix}access_token"
    return f"{prefix}refresh_token"


def cookie_settings():
    """
    Uses your chosen setting names:
    - SECURE_COOKIES (bool)
    - JWT_COOKIE_SAMESITE ("Lax"/"Strict"/"None")
    - JWT_COOKIE_DOMAIN (str|None)
    - JWT_COOKIE_PATH (str)
    """
    secure = getattr(settings, "SECURE_COOKIES", True)
    samesite = getattr(settings, "JWT_COOKIE_SAMESITE", "None")
    domain = getattr(settings, "JWT_COOKIE_DOMAIN", None)
    path = getattr(settings, "JWT_COOKIE_PATH", "/")
    return secure, samesite, domain, path


def set_auth_cookies(response, access, refresh):
    set_access_cookie(response, access)
    set_refresh_cookie(response, refresh)


def set_access_cookie(response, access):
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
    _, _, domain, path = cookie_settings()
    response.delete_cookie(cookie_name("access"), domain=domain, path=path)
    response.delete_cookie(cookie_name("refresh"), domain=domain, path=path)