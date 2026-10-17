from django.conf import settings
from django.core.mail import send_mail


def send_enquiry_notification(enquiry):
    if not settings.STAFF_NOTIFICATION_EMAIL:
        return
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
    )