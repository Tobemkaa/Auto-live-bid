# marketing/emails.py
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


def send_enquiry_notification(enquiry):
    if not settings.STAFF_NOTIFICATION_EMAIL:
        return
    try:
        send_mail(
            subject=f"New enquiry from {enquiry.name}",
            message=(
                f"Name: {enquiry.name}\n"
                f"Phone: {enquiry.phone}\n"
                f"Email: {enquiry.email or '—'}\n\n"
                f"{enquiry.message}"
            ),
            from_email=None,
            recipient_list=[settings.STAFF_NOTIFICATION_EMAIL],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send enquiry notification for enquiry %s", enquiry.pk)