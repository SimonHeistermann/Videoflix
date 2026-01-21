from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_activation_email(email, activation_link):
    context = {"activation_link": activation_link}
    _send_templated_email(
        to_email=email,
        subject="Confirm your email",
        template_name="user_auth_app/email_activation.html",
        context=context,
    )


def send_passwordreset_email(email, passwordreset_link):
    context = {"reset_link": passwordreset_link}
    _send_templated_email(
        to_email=email,
        subject="Reset your password",
        template_name="user_auth_app/email_reset.html",
        context=context,
    )


def _send_templated_email(to_email, subject, template_name, context):
    html = render_to_string(template_name, context)
    text = strip_tags(html)

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    msg.attach_alternative(html, "text/html")
    _attach_inline_logo_if_exists(msg)
    msg.send(fail_silently=False)


def _attach_inline_logo_if_exists(msg):
    logo_path = _logo_path()
    if not logo_path.exists():
        return

    with logo_path.open("rb") as img:
        image = MIMEImage(img.read())
        image.add_header("Content-ID", "<logo>")
        image.add_header("Content-Disposition", "inline", filename=logo_path.name)
        msg.attach(image)


def _logo_path():
    custom = getattr(settings, "EMAIL_LOGO_PATH", "") or ""
    if custom:
        return Path(custom)
    return Path(settings.BASE_DIR) / "assets" / "logo_icon.png"