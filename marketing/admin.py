from django.contrib import admin
from customers.models import Customer
from .models import Enquiry



@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email", "created_at", "handled")
    list_filter = ("handled",)
    actions = ["convert_to_customer"]

    @admin.action(description="Convert selected enquiries to customers")
    def convert_to_customer(self, request, queryset):
        created = 0
        for enquiry in queryset:
            customer, was_created = Customer.objects.get_or_create(
                phone=enquiry.phone,
                defaults={"name": enquiry.name, "email": enquiry.email},
            )
            if was_created:
                created += 1
            enquiry.handled = True
            enquiry.save(update_fields=["handled"])
        self.message_user(request, f"Created {created} new customer(s).")


# Register your models here.
