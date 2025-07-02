from django.shortcuts import render, redirect, get_object_or_404
from events.models import Event, Participant, Category
from events.forms import EventForm, CategoryForm, ParticipantForm
from django.db.models import Count
from django.utils.timezone import now
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

# Dashboard view with stats + today's events
def dashboard_view(request):
    today = now().date()
    counts = {
        "events": Event.objects.count(),
        "participants": Participant.objects.count(),
        "categories": Category.objects.count(),
    }
    today_events = Event.objects.select_related('category').filter(date=today).order_by('time')

    context = {
        "counts": counts,
        "today_events": today_events,
    }
    return render(request, "events/dashboard.html", context)

# Event List with participants count prefetch
def event_list(request):
    events = Event.objects.select_related("category").prefetch_related("participants").all()
    return render(request, "events/event_list.html", {"events": events})

# Event Create
def create_event(request):
    form = EventForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('event-list')
    return render(request, "events/event_form.html", {"form": form, "title": "Create Event"})

# Event Update
def update_event(request, id):
    event = get_object_or_404(Event, id=id)
    form = EventForm(request.POST or None, instance=event)
    if form.is_valid():
        form.save()
        return redirect('event-list')
    return render(request, "events/event_form.html", {"form": form, "title": "Edit Event"})

# Event Delete
@require_http_methods(["POST"])
def delete_event(request, id):
    event = get_object_or_404(Event, id=id)
    event.delete()
    return redirect('event-list')


# Category List
def category_list(request):
    categories = Category.objects.all()
    return render(request, "events/category_list.html", {"categories": categories})

# Category Create
def create_category(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('category-list')
    return render(request, "events/category_form.html", {"form": form, "title": "Create Category"})

# Category Update
def update_category(request, id):
    category = get_object_or_404(Category, id=id)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('category-list')
    return render(request, "events/category_form.html", {"form": form, "title": "Edit Category"})

# Category Delete
@require_http_methods(["POST"])
def delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    return redirect('category-list')


# Participant List
def participant_list(request):
    participants = Participant.objects.prefetch_related("events").all()
    return render(request, "events/participant_list.html", {"participants": participants})

# Participant Create
def create_participant(request):
    form = ParticipantForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('participant-list')
    return render(request, "events/participant_form.html", {"form": form, "title": "Create Participant"})

# Participant Update
def update_participant(request, id):
    participant = get_object_or_404(Participant, id=id)
    form = ParticipantForm(request.POST or None, instance=participant)
    if form.is_valid():
        form.save()
        return redirect('participant-list')
    return render(request, "events/participant_form.html", {"form": form, "title": "Edit Participant"})

# Participant Delete
@require_http_methods(["POST"])
def delete_participant(request, id):
    participant = get_object_or_404(Participant, id=id)
    participant.delete()
    return redirect('participant-list')