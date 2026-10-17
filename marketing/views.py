from django.shortcuts import render, redirect
from django.contrib import messages
from orders.models import Vehicle
from .forms import ContactForm
from .models import Enquiry
from .emails import send_enquiry_notification
from django.db.models import Q
from urllib.parse import quote


def home(request):
    return render(request, "marketing/home.html")


def about(request):
    return render(request, "marketing/about.html")


def services(request):
    return render(request, "marketing/services.html")


def testimonials(request):
    return render(request, "marketing/testimonials.html")


def inventory(request):
    vehicles = Vehicle.objects.filter(order__isnull=True, stage=Vehicle.Stage.AVAILABLE)

    query = request.GET.get("q", "").strip()
    if query:
        vehicles = vehicles.filter(Q(make__icontains=query) | Q(model__icontains=query))

    selected_makes = request.GET.getlist("make")
    if selected_makes:
        vehicles = vehicles.filter(make__in=selected_makes)

    price_min = request.GET.get("price_min", "")
    price_max = request.GET.get("price_max", "")
    if price_min:
        vehicles = vehicles.filter(asking_price__gte=price_min)
    if price_max:
        vehicles = vehicles.filter(asking_price__lte=price_max)

    sort = request.GET.get("sort", "newest")
    sort_map = {"newest": "-created_at", "price_low": "asking_price", "price_high": "-asking_price"}
    vehicles = vehicles.order_by(sort_map.get(sort, "-created_at"))

    all_makes = Vehicle.objects.filter(
        order__isnull=True, stage=Vehicle.Stage.AVAILABLE
    ).values_list("make", flat=True).distinct().order_by("make")

    vehicles = list(vehicles)  # materialize so we can attach a computed attribute below
    for v in vehicles:
        price_note = f"(${v.asking_price:,.0f})" if v.asking_price else ""
        message = f"Hi, I'm interested in the {v.year} {v.make} {v.model} {price_note}".strip()
        v.whatsapp_text = quote(message)

    return render(request, "marketing/inventory.html", {
        "vehicles": vehicles,
        "count": len(vehicles),
        "query": query,
        "all_makes": all_makes,
        "selected_makes": selected_makes,
        "price_min": price_min,
        "price_max": price_max,
        "sort": sort,
    })
    


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            enquiry = Enquiry.objects.create(**form.cleaned_data)
            send_enquiry_notification(enquiry)
            messages.success(request, "Thanks — we'll get back to you shortly.")
            return redirect("marketing_home")
    else:
        form = ContactForm()
    return render(request, "marketing/contact.html", {"form": form})



# Create your views here.
