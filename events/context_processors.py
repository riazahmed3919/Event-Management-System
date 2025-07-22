def user_roles(request):
    if request.user.is_authenticated:
        return {
            'is_admin': request.user.is_superuser,
            'is_organizer': request.user.groups.filter(name='Organizer').exists(),
            'is_participant': request.user.groups.filter(name='Participant').exists(),
        }
    return {}