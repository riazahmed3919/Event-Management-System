from django.urls import path
from . import views

urlpatterns = [
    path('', views.public_home, name='public-home'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('access-restricted/', views.access_restricted, name='access-restricted'),

    # User list for admins
    path('users/', views.user_list, name='user-list'),

    # Redirect
    path('redirect-after-login/', views.redirect_after_login, name='redirect-after-login'),

    # Dashboards
    path('dashboard/admin/', views.admin_dashboard, name='admin-dashboard'),
    path('organizer/dashboard/', views.organizer_dashboard, name='organizer-dashboard'),
    path('participant/dashboard/', views.participant_dashboard, name='participant-dashboard'),

    # Event
    path('events/', views.event_list, name='event-list'),
    path('events/create/', views.create_event, name='event-create'),
    path('events/<int:id>/edit/', views.update_event, name='event-update'),
    path('events/<int:id>/delete/', views.delete_event, name='event-delete'),

    # Category
    path('categories/', views.category_list, name='category-list'),
    path('categories/create/', views.create_category, name='category-create'),
    path('categories/<int:id>/edit/', views.update_category, name='category-update'),
    path('categories/<int:id>/delete/', views.delete_category, name='category-delete'),

    # Participant
    path('participants/', views.participant_list, name='participant-list'),
    path('participants/add/', views.participant_add, name='participant-add'),
    path('participants/<int:id>/', views.participant_detail, name='participant-detail'),
    path('participants/<int:id>/edit/', views.participant_edit, name='participant-edit'),
    path('participants/<int:id>/delete/', views.delete_participant, name='participant-delete'),
    path('participant/participants/', views.participant_list_view, name='participant-participants-list'),

    # Groups
    path('groups/', views.group_list, name='group-list'),
    path('groups/create/', views.group_create, name='group-create'),
    path('groups/<int:id>/edit/', views.group_update, name='group-update'),
    path('groups/<int:id>/delete/', views.delete_group, name='group-delete'),

    # RSVP
    path("events/<int:event_id>/rsvp/", views.rsvp_event, name="rsvp-event"),
    path('events/<int:event_id>/cancel_rsvp/', views.cancel_rsvp, name='cancel-rsvp'),
]