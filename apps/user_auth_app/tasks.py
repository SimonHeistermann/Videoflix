"""
Email task utilities for the user authentication flow.

Provides task functions to send activation and password reset emails
using Django's templating system and EmailMultiAlternatives.

If an inline logo exists, it is attached with Content-ID <logo> so it can be
referenced from HTML templates (e.g., <img src="cid:logo" />).
"""

from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_activation_email(email, activation_link):
    """
    Send an account activation email to the given address.

    Args:
        email (str): Recipient email address.
        activation_link (str): Frontend link used to activate the account.
    """
    context = {"activation_link": activation_link}
    _send_templated_email(
        to_email=email,
        subject="Confirm your email",
        template_name="user_auth_app/email_activation.html",
        context=context,
    )


def send_passwordreset_email(email, passwordreset_link):
    """
    Send a password reset email to the given address.

    Args:
        email (str): Recipient email address.
        passwordreset_link (str): Frontend link used to reset the password.
    """
    context = {"reset_link": passwordreset_link}
    _send_templated_email(
        to_email=email,
        subject="Reset your password",
        template_name="user_auth_app/email_reset.html",
        context=context,
    )


def _send_templated_email(to_email, subject, template_name, context):
    """
    Render an HTML email template and send it as multipart (text + HTML).

    Args:
        to_email (str): Recipient email address.
        subject (str): Email subject line.
        template_name (str): Django template path for the HTML body.
        context (dict): Context variables for template rendering.
    """
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
    """
    Attach an inline logo image to the email message if it exists.

    The image is attached with:
        Content-ID: <logo>
        Content-Disposition: inline

    Args:
        msg (EmailMultiAlternatives): The email message to attach the image to.
    """
    logo_path = _logo_path()
    if not logo_path.exists():
        return

    with logo_path.open("rb") as img:
        image = MIMEImage(img.read())
        image.add_header("Content-ID", "<logo>")
        image.add_header("Content-Disposition", "inline", filename=logo_path.name)
        msg.attach(image)


def _logo_path():
    """
    Resolve the logo path from settings.

    If EMAIL_LOGO_PATH is set, it is used. Otherwise, a default path relative
    to BASE_DIR is used.

    Returns:
        pathlib.Path: Resolved logo path.
    """
    custom = getattr(settings, "EMAIL_LOGO_PATH", "") or ""
    if custom:
        return Path(custom)
    return Path(settings.BASE_DIR) / "assets" / "logo_icon.png"