# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Payment
from .emails import send_payment_receipt


@receiver(post_save, sender=Payment)
def payment_saved(sender, instance, created, **kwargs):
    if created:
        send_payment_receipt(instance)