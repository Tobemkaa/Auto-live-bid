from django.contrib import admin
from .models import Order, Vehicle, StatusHistory, CostItem, Payment
from django import forms

class VehicleInline(admin.TabularInline):
    model = Vehicle
    extra = 1
    fields = ("make", "model", "year", "lot_number", "stage", "max_bid", "service_fee")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "order_type", "status", "balance_display", "created_at")
    list_filter = ("order_type", "status")
    search_fields = ("customer__name", "customer__phone")
    autocomplete_fields = ("customer",)
    readonly_fields = ("created_by", "balance_display")
    inlines = [VehicleInline]

    @admin.display(description="Balance (USD)")
    def balance_display(self, obj):
        bal = obj.balance()
        if bal < 0:
            return f"Credit held: ${abs(bal):,.2f}"
        return f"${bal:,.2f} owed"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields["order_type"].help_text = (
            "Car sourcing: add new vehicle(s) below. "
            "Stock sale: leave vehicles empty here — instead, "
            "go to the existing vehicle in Vehicles and set its Order field."
        )
        return form

class CostItemInline(admin.TabularInline):
    model = CostItem
    extra = 1
    fields = ("category", "amount_usd", "date_incurred", "note", "adjusts")
    fk_name = "vehicle"


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("__str__", "order", "stage", "lot_number")
    list_filter = ("stage",)
    search_fields = ("vin", "lot_number", "make", "model")
    readonly_fields = ("stage",)  # stage is view-only here
    fields = ("order", "vin", "lot_number", "copart_url", "make", "model", "year",
              "stage", "max_bid", "service_fee", "asking_price", "sale_price", "photo")
    actions = ["change_stage_action"]
    inlines = [CostItemInline]
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if isinstance(obj, CostItem) and obj.pk is None:
                obj.recorded_by = request.user
            obj.save()
        formset.save_m2m()
    
    @admin.action(description="Change stage of selected vehicles")
    def change_stage_action(self, request, queryset):
        if "apply" in request.POST:
            form = ChangeStageForm(request.POST)
            if form.is_valid():
                new_stage = form.cleaned_data["new_stage"]
                note = form.cleaned_data["note"]
                for vehicle in queryset:
                    vehicle.change_stage(new_stage, request.user, note=note)
                self.message_user(request, f"Updated {queryset.count()} vehicle(s).")
                return None
        else:
            form = ChangeStageForm()

        from django.shortcuts import render
        return render(request, "admin/change_stage.html", {
            "vehicles": queryset,
            "form": form,
        })

@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "from_stage", "to_stage", "changed_by", "changed_at")
    list_filter = ("to_stage",)
    readonly_fields = [f.name for f in StatusHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(CostItem)
class CostItemAdmin(admin.ModelAdmin):
    list_display = ("category", "amount_usd", "vehicle", "order", "date_incurred")
    list_filter = ("category",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "kind", "currency", "amount", "amount_usd", "paid_on")
    list_filter = ("kind", "currency")
    readonly_fields = ("amount_usd",)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # normal staff can't delete payments

    def has_change_permission(self, request, obj=None):
        return obj is None or request.user.is_superuser  # add-only for regular staff
# Register your models here.
class ChangeStageForm(forms.Form):
    new_stage = forms.ChoiceField(choices=Vehicle.Stage.choices)
    note = forms.CharField(required=False, widget=forms.Textarea)
