from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_payment_receipt(payment):
    customer = payment.order.customer
    if not customer.email:
        return  # nothing to send to; caller can check this
    body = render_to_string("orders/emails/payment_receipt.txt", {
        "payment": payment,
        "balance": payment.order.balance(),
    })
    send_mail(
        subject=f"Payment received — Order #{payment.order.pk}",
        message=body,
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=[customer.email],
    )