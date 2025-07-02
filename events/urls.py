from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),

    # Event urls
    path('events/', views.event_list, name='event-list'),
    path('events/create/', views.create_event, name='event-create'),
    path('events/<int:id>/edit/', views.update_event, name='event-update'),
    path('events/<int:id>/delete/', views.delete_event, name='event-delete'),

    # Category urls
    path('categories/', views.category_list, name='category-list'),
    path('categories/create/', views.create_category, name='category-create'),
    path('categories/<int:id>/edit/', views.update_category, name='category-update'),
    path('categories/<int:id>/delete/', views.delete_category, name='category-delete'),

    # Participant urls
    path('participants/', views.participant_list, name='participant-list'),
    path('participants/create/', views.create_participant, name='participant-create'),
    path('participants/<int:id>/edit/', views.update_participant, name='participant-update'),
    path('participants/<int:id>/delete/', views.delete_participant, name='participant-delete'),
]