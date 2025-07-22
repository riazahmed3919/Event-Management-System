from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from events.models import Event, Category
from events.forms import EventForm, CategoryForm
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Prefetch

# Role checkers
def is_admin(user):
    return user.is_superuser

def is_organizer(user):
    return user.groups.filter(name='Organizer').exists()

def is_participant(user):
    return user.groups.filter(name='Participant').exists()

def is_admin_or_organizer_or_participant(user):
    return is_admin(user) or is_organizer(user) or is_participant(user)

# Public home
def public_home(request):
    total_events = Event.objects.count()
    total_participants = User.objects.filter(groups__name='Participant').count()
    total_categories = Category.objects.count()

    context = {
        "total_events": total_events,
        "total_participants": total_participants,
        "total_categories": total_categories,
    }

    return render(request, "events/public_home.html", context)

# Signup
def signup(request):
    form_errors = {}

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")

        if not username:
            form_errors["username"] = "Username is required."
        elif User.objects.filter(username=username).exists():
            form_errors["username"] = "Username already exists."

        if not email:
            form_errors["email"] = "Email is required."
        elif User.objects.filter(email=email).exists():
            form_errors["email"] = "Email is already registered."

        if not password1:
            form_errors["password1"] = "Password is required."

        if not password2:
            form_errors["password2"] = "Please confirm your password."

        if password1 and password2 and password1 != password2:
            form_errors["password2"] = "Passwords do not match."

        if not form_errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            participant_group, _ = Group.objects.get_or_create(name='Participant')
            user.groups.add(participant_group)
            messages.success(request, "Account created successfully! Please log in.")
            return redirect('login')

        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, "events/signup.html", {"form_errors": form_errors})

# Login
def custom_login(request):
    if request.user.is_authenticated:
        return redirect('redirect-after-login')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('redirect-after-login')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'events/login.html')

# Logout
@login_required
def custom_logout(request):
    logout(request)
    return redirect('public-home')

# Admin dashboard
@user_passes_test(is_admin)
def admin_dashboard(request):
    today = now().date()
    counts = {
        "events": Event.objects.count(),
        "categories": Category.objects.count(),
        "participants": User.objects.filter(groups__name="Participant").count(),
        "groups": Group.objects.count(),
        "today_events": Event.objects.filter(date=today).count(),
    }

    context = {
        "counts": counts,
        "today": today,
    }
    return render(request, "events/admin_dashboard.html", context)

# Organizer Dashboard
@login_required
@user_passes_test(is_organizer)
def organizer_dashboard(request):
    total_events = Event.objects.count()
    total_categories = Category.objects.count()
    total_participants = User.objects.filter(groups__name='Participant').count()

    context = {
        "counts": {
            "events": total_events,
            "categories": total_categories,
            "participants": total_participants,
        }
    }
    return render(request, 'events/organizer_dashboard.html', context)

# Participant Dashboard
@login_required
@user_passes_test(is_participant)
def participant_dashboard(request):
    return render(request, 'events/participant_dashboard.html')

# Participant-only participants list
@login_required
@user_passes_test(is_participant)
def participant_list_view(request):
    participants = User.objects.filter(groups__name='Participant').prefetch_related(
        Prefetch('rsvp_events', queryset=Event.objects.all())
    ).order_by('username')

    return render(request, 'events/participant_list_view.html', {
        'participants': participants,
    })

# Redirect after login
@login_required
def redirect_after_login(request):
    user = request.user
    if is_admin(user):
        return redirect('admin-dashboard')
    elif is_organizer(user):
        return redirect('organizer-dashboard')
    elif is_participant(user):
        return redirect('participant-dashboard')
    else:
        return redirect('public-home')

# Event Views
@login_required
def event_list(request):
    events = Event.objects.select_related("category").prefetch_related("participants").all()
    return render(request, "events/event_list.html", {"events": events})

@login_required
def create_event(request):
    form = EventForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('event-list')
    return render(request, "events/event_form.html", {"form": form, "title": "Create Event"})

@login_required
def update_event(request, id):
    event = get_object_or_404(Event, id=id)
    form = EventForm(request.POST or None, instance=event)
    if form.is_valid():
        form.save()
        return redirect('event-list')
    return render(request, "events/event_form.html", {"form": form, "title": "Edit Event"})

@login_required
@require_http_methods(["POST"])
def delete_event(request, id):
    event = get_object_or_404(Event, id=id)
    event.delete()
    return redirect('event-list')

# Category Views
@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, "events/category_list.html", {"categories": categories})

@login_required
def create_category(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('category-list')
    return render(request, "events/category_form.html", {"form": form, "title": "Create Category"})

@login_required
def update_category(request, id):
    category = get_object_or_404(Category, id=id)
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('category-list')
    return render(request, "events/category_form.html", {"form": form, "title": "Edit Category"})

@login_required
@require_http_methods(["POST"])
def delete_category(request, id):
    category = get_object_or_404(Category, id=id)
    category.delete()
    return redirect('category-list')

# Participant Views
@login_required
def participant_list(request):
    user = request.user
    if not is_admin_or_organizer_or_participant(user):
        return redirect('login')

    if is_participant(user):
        return redirect('participant-participants-list')

    participants = User.objects.filter(groups__name='Participant').order_by('username')
    is_admin_flag = is_admin(user)

    return render(request, 'events/participant_list.html', {
        'participants': participants,
        'is_admin': is_admin_flag,
    })

@login_required
@user_passes_test(is_admin)
def participant_add(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()

            participant_group, _ = Group.objects.get_or_create(name='Participant')
            user.groups.add(participant_group)
            messages.success(request, "Participant added successfully!")
            return redirect('participant-list')

    return render(request, 'events/participant_add.html')

@login_required
@user_passes_test(is_admin)
def participant_detail(request, id):
    participant = get_object_or_404(User, id=id)
    groups = Group.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')

        participant.username = username
        participant.first_name = first_name
        participant.last_name = last_name
        participant.email = email
        participant.save()

        selected_groups = request.POST.getlist('groups')
        participant.groups.clear()
        for group_id in selected_groups:
            try:
                group = Group.objects.get(id=group_id)
                participant.groups.add(group)
            except Group.DoesNotExist:
                pass

        messages.success(request, "User updated successfully!")
        return redirect('participant-detail', id=participant.id)

    context = {
        'participant': participant,
        'groups': groups,
    }
    return render(request, 'events/participant_detail.html', context)

@login_required
@user_passes_test(is_admin)
def participant_edit(request, id):
    participant = get_object_or_404(User, id=id)
    groups = Group.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        selected_groups = request.POST.getlist('groups')

        if not username:
            messages.error(request, "Username cannot be empty.")
        else:
            if User.objects.filter(username=username).exclude(id=participant.id).exists():
                messages.error(request, "Username already exists.")
            else:
                participant.username = username
                participant.email = email
                participant.first_name = first_name
                participant.last_name = last_name
                participant.save()

                participant.groups.clear()
                for group_id in selected_groups:
                    try:
                        group = Group.objects.get(id=group_id)
                        participant.groups.add(group)
                    except Group.DoesNotExist:
                        pass

                messages.success(request, "Participant updated successfully!")
                return redirect('participant-list')

    context = {
        'participant': participant,
        'groups': groups,
    }
    return render(request, 'events/participant_edit.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_participant(request, id):
    participant = get_object_or_404(User, id=id)
    participant.delete()
    messages.success(request, "Participant deleted successfully!")
    return redirect('participant-list')

# Group Views
@user_passes_test(is_admin)
def group_list(request):
    groups = Group.objects.all()
    return render(request, "events/group_list.html", {"groups": groups})

@user_passes_test(is_admin)
def group_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Group.objects.get_or_create(name=name)
            return redirect('group-list')
    return render(request, "events/group_form.html", {"title": "Create Group"})

@user_passes_test(is_admin)
def group_update(request, id):
    group = get_object_or_404(Group, id=id)
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            group.name = name
            group.save()
            return redirect('group-list')
    return render(request, "events/group_form.html", {"group": group, "title": "Edit Group"})

@user_passes_test(is_admin)
@require_http_methods(["POST"])
def delete_group(request, id):
    group = get_object_or_404(Group, id=id)
    group.delete()
    messages.success(request, "Group deleted successfully!")
    return redirect('group-list')

# User list for admins only
@login_required
@user_passes_test(is_admin)
def user_list(request):
    role_filter = request.GET.get('role', 'all')
    roles = ['Admin', 'Organizer', 'Participant']

    if role_filter == 'admin':
        users = User.objects.filter(is_superuser=True)
    elif role_filter == 'organizer':
        users = User.objects.filter(groups__name='Organizer')
    elif role_filter == 'participant':
        users = User.objects.filter(groups__name='Participant')
    else:
        users = User.objects.all()

    users = users.prefetch_related('groups').order_by('username')

    context = {
        'users': users,
        'role_filter': role_filter,
        'roles': roles,
    }
    return render(request, 'events/user_list.html', context)