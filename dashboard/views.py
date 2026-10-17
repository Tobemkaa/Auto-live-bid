from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from orders.models import Order, Vehicle


@login_required
def home(request):
    open_orders = Order.objects.filter(status=Order.Status.OPEN).select_related("customer")

    orders_with_balance = [{"order": o, "balance": o.balance()} for o in open_orders]
    unpaid = [row for row in orders_with_balance if row["balance"] > 0]
    total_outstanding = sum((row["balance"] for row in unpaid), Decimal("0"))

    vehicles_by_stage = Vehicle.objects.values("stage").annotate(count=Count("id")).order_by("stage")

    unsold_stock = Vehicle.objects.filter(order__isnull=True, stage=Vehicle.Stage.AVAILABLE)
    awaiting_decision = Vehicle.objects.filter(
        stage=Vehicle.Stage.AWAITING_DECISION
    ).select_related("order__customer")

    context = {
        "unpaid_orders": unpaid,
        "unpaid_count": len(unpaid),
        "total_outstanding": total_outstanding,
        "vehicles_by_stage": vehicles_by_stage,
        "unsold_stock": unsold_stock,
        "unsold_count": unsold_stock.count(),
        "awaiting_decision": awaiting_decision,
        "awaiting_count": awaiting_decision.count(),
    }
    return render(request, "dashboard/home.html", context)