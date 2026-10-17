from django.db import models
from django.conf import settings
from decimal import Decimal

class Order(models.Model):
    class Type(models.TextChoices):
        CAR_SOURCING = "car_sourcing", "Car_sourcing"
        STOCK_SALE = "stock_sale", "Stock_sale"
        BULK_SOURCING = "bulk_sourcing", "Bulk_sourcing"
        
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        
    customer = models.ForeignKey("customers.Customer", on_delete=models.PROTECT, related_name="orders")
    order_type = models.CharField(max_length=20, choices=Type.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders_created")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Order #{self.pk} - {self.customer.name}"
    
    def total_cost(self):
        """Sum of costs across the order's vehicles, plus order-level costs.
        A stock-sale vehicle uses its agreed sale_price instead of costs+fee,
        since that price is negotiated separately, not built from a formula.
        Lost and still-undecided vehicles are excluded."""
        excluded_stages = [Vehicle.Stage.LOST, Vehicle.Stage.AWAITING_DECISION]
        total = Decimal("0")

        for vehicle in self.vehicles.exclude(stage__in=excluded_stages):
            if self.order_type == self.Type.STOCK_SALE and vehicle.sale_price is not None:
                total += vehicle.sale_price
            else:
                vehicle_costs = vehicle.costs.aggregate(total=models.Sum("amount_usd"))["total"] or Decimal("0")
                total += vehicle_costs + vehicle.service_fee

        order_costs = self.costs.filter(vehicle__isnull=True).aggregate(
            total=models.Sum("amount_usd")
        )["total"] or Decimal("0")
        total += order_costs

        return total    
        
    
    def total_paid(self):
        return self.payments.aggregate(total=models.Sum("amount_usd"))["total"] or Decimal("0")

    def balance(self):
        return self.total_cost() - self.total_paid()
    
    
class Vehicle(models.Model):
    class Stage(models.TextChoices):
        BID_PENDING = "bid_pending", "Bid pending"
        WON = "won", "Won"
        AWAITING_DECISION = "awaiting_decision", "Lost, awaiting customer decision"
        LOST = "lost", "Lost (closed)"
        PAID_TO_COPART = "paid_to_copart", "Paid to Copart"
        IN_US = "in_us", "In US"
        SHIPPED = "shipped", "Shipped"
        ARRIVED = "arrived", "Arrived in Nigeria"
        CLEARING = "clearing", "Clearing"
        REFURBISHING = "refurbishing", "Refurbishing"
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        SOLD = "sold", "Sold"
        DELIVERED = "delivered", "Delivered"
        
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.PROTECT, related_name="vehicles")
    vin = models.CharField(max_length=17, unique=True, null=True, blank=True)
    lot_number = models.CharField(max_length=30, blank=True)
    copart_url = models.URLField(blank=True)
    make = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveSmallIntegerField()
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.BID_PENDING)
    max_bid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    service_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    asking_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    sale_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    photo = models.ImageField(upload_to="vehicles/", blank=True, null=True)
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model}"
    
    def change_stage(self, new_stage, user, note=""):
        old_stage = self.stage
        if old_stage == new_stage:
            return
        self.stage = new_stage
        self.save(update_fields=["stage", "updated_at"])
        StatusHistory.objects.create(
            vehicle=self,
            from_stage=old_stage,
            to_stage=new_stage,
            changed_by=user,
            note=note,
        )

class StatusHistory(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="status_history")
    from_stage = models.CharField(max_length=20, choices=Vehicle.Stage.choices, blank=True)
    to_stage = models.CharField(max_length=20, choices=Vehicle.Stage.choices)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True)
    
    class Meta:
        ordering = ["-changed_at"]
        verbose_name_plural = "Status history"

    def __str__(self):
        return f"{self.vehicle} : {self.from_stage or 'new'} -> {self.to_stage}"
    
class CostItem(models.Model):
    class Category(models.TextChoices):
        AUCTION_BID = "auction_bid", "Auction bid"
        COPART_FEES = "copart_fees", "Copart fees"
        SHIPPING = "shipping", "Shipping"
        CUSTOMS_DUTY = "customs_duty", "Customs and duty"
        CLEARING = "clearing", "Clearing"
        REPAIR = "repair", "Repair / refurbishment"
        HANDLING = "handling", "Handling"
        OTHER = "other", "Other"

    vehicle = models.ForeignKey(
        Vehicle, null=True, blank=True, on_delete=models.PROTECT, related_name="costs"
    )
    order = models.ForeignKey(
        Order, null=True, blank=True, on_delete=models.PROTECT, related_name="costs"
    )
    category = models.CharField(max_length=20, choices=Category.choices)
    amount_usd = models.DecimalField(max_digits=12, decimal_places=2)
    date_incurred = models.DateField()
    note = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    adjusts = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT,
        related_name="adjustments",
        help_text="If this is a correction to an earlier estimate, link it here."
    )
    
    def __str__(self):
        label = f"{self.get_category_display()}: ${self.amount_usd}"
        return f"{label} (adjustment)" if self.adjusts_id else label

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.vehicle_id and not self.order_id:
            raise ValidationError("A cost item must be linked to a vehicle or an order.")

    def __str__(self):
        return f"{self.get_category_display()}: ${self.amount_usd}"
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(vehicle__isnull=False) | models.Q(order__isnull=False),
                name="cost_item_has_vehicle_or_order",
            )
        ]



class Payment(models.Model):
    class Kind(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        INSTALLMENT = "installment", "Installment"
        FINAL = "final", "Final payment"
        REFUND = "refund", "Refund"
        TRANSFER_OUT = "transfer_out", "Transfer out"
        TRANSFER_IN = "transfer_in", "Transfer in"

    class Currency(models.TextChoices):
        USD = "USD", "US Dollar"
        NGN = "NGN", "Naira"

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="payments")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    currency = models.CharField(max_length=3, choices=Currency.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    ngn_per_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_usd = models.DecimalField(max_digits=14, decimal_places=2, editable=False)
    paid_on = models.DateField()
    method = models.CharField(max_length=20, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-paid_on", "-created_at"]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.currency == self.Currency.NGN and not self.ngn_per_usd:
            raise ValidationError("An exchange rate is required for naira payments.")

    def save(self, *args, **kwargs):
        if self.currency == self.Currency.USD:
            self.amount_usd = self.amount
        else:
            self.amount_usd = (self.amount / self.ngn_per_usd).quantize(Decimal("0.01"))
            
        if self.kind in (self.Kind.REFUND, self.Kind.TRANSFER_OUT) and self.amount_usd > 0:
            self.amount_usd = -self.amount_usd
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_kind_display()} - ${self.amount_usd} ({self.order})"        





# Create your models here.
