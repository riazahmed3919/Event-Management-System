from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Event, Category
from .forms import EventForm, CategoryForm, EditProfileForm, CustomPasswordChangeForm
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods
from django.db.models import Prefetch
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.views.generic import TemplateView, UpdateView
from django.views import View
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

User = get_user_model()
CustomUser = get_user_model()

# Role checkers
def is_admin(user):
    return user.is_superuser

def is_organizer(user):
    return user.groups.filter(name='Organizer').exists()

def is_participant(user):
    return user.groups.filter(name='Participant').exists()

def is_admin_or_organizer_or_participant(user):
    return is_admin(user) or is_organizer(user) or is_participant(user)

# CBV for Public Home View
class PublicHomeView(TemplateView):
    template_name = 'events/public_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_events'] = Event.objects.count()
        context['total_participants'] = User.objects.filter(groups__name='Participant').count()
        context['total_categories'] = Category.objects.count()
        context['upcoming_events'] = Event.objects.filter(date__gte=now().date()).order_by('date')[:2]

        return context

# CBV for Signup View
class SignupView(View):
    template_name = "events/signup.html"

    def get(self, request):
        return render(request, self.template_name, {"form_errors": {}})

    def post(self, request):
        form_errors = {}

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
                is_active=False
            )
            user.save()

            participant_group, _ = Group.objects.get_or_create(name='Participant')
            user.groups.add(participant_group)

            messages.success(request, "Account created successfully! Please check your email to activate your account.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")

        return render(request, self.template_name, {"form_errors": form_errors})

# Activate Account
def activate_account(request, uidb64, token):
    try:
        # Decode the uid from base64 to user id
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated successfully! You can now log in.")
        return redirect('login')
    else:
        messages.error(request, "The activation link is invalid or expired.")
        return render(request, "events/activation_invalid.html")

# CBV for Custom Login Form
class CustomLoginView(LoginView):
    template_name = 'events/login.html'
    
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, "Your account is inactive. Please activate your account via email.")
                return self.form_invalid(self.get_form())
            else:
                login(request, user)
                return redirect('redirect-after-login')
        else:
            if not User.objects.filter(username=username).exists():
                return redirect('access-restricted')
            else:
                messages.error(request, "Invalid username or password.")
                return self.form_invalid(self.get_form())

# CBV for Custom Logout View
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('public-home')

# CBV for Admin Dashboard View
@method_decorator(user_passes_test(is_admin), name='dispatch')
class AdminDashboardView(TemplateView):
    template_name = 'events/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = now().date()
        context['today'] = today
        context['counts'] = {
            "events": Event.objects.count(),
            "categories": Category.objects.count(),
            "participants": User.objects.filter(groups__name="Participant").count(),
            "groups": Group.objects.count(),
            "today_events": Event.objects.filter(date=today).count(),
        }
        return context

# CBV for Organizer Dashboard View
organizer_dashboard_decorator = [login_required, user_passes_test(is_organizer)]
@method_decorator(organizer_dashboard_decorator, name='dispatch')
class OrganizerDashboardView(TemplateView):
    template_name = 'events/organizer_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['counts'] = {
            "events": Event.objects.count(),
            "categories": Category.objects.count(),
            "participants": User.objects.filter(groups__name='Participant').count(),
        }
        return context

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
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('event-list')
    else:
        form = EventForm()
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

# RSVP
@login_required
@user_passes_test(is_participant)
def rsvp_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user in event.participants.all():
        messages.warning(request, "You have already RSVPed for this event!")
    else:
        event.participants.add(request.user)
        messages.success(request, "You have successfully RSVPed for this event!")

    return redirect('event-list')

@login_required
def cancel_rsvp(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user in event.participants.all():
        event.participants.remove(request.user)
        messages.success(request, "Your RSVP has been cancelled.")
    else:
        messages.warning(request, "You have not RSVPed for this event.")

    return redirect('event-list')

# Restriction
def access_restricted(request):
    return render(request, "events/access_restricted.html")

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['profile_image'] = user.profile_image
        context['name'] = user.get_full_name() or user.username
        context['email'] = user.email
        context['phone_number'] = user.phone_number
        context['username'] = user.username
        context['member_since'] = user.date_joined
        context['last_login'] = user.last_login
        return context
    
class EditProfileView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = EditProfileForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user
    
class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('profile')