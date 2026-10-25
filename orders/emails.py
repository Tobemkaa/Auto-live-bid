# orders/emails.py
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)


def send_payment_receipt(payment):
    customer = payment.order.customer
    if not customer.email:
        return
    body = render_to_string("orders/emails/payment_receipt.txt", {
        "payment": payment,
        "balance": payment.order.balance(),
    })
    try:
        send_mail(
            subject=f"Payment received — Order #{payment.order.pk}",
            message=body,
            from_email=None,
            recipient_list=[customer.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send payment receipt for payment %s", payment.pk)