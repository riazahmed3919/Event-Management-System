from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    profile_image = models.ImageField(upload_to='profile/', default='profile/default.jpg')
    phone_number = models.CharField(max_length=11, blank=True, null=True)

    def __str__(self):
        return self.username

class Event(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=250)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, related_name="events")
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="rsvp_events", blank=True)
    image = models.ImageField(upload_to='events/', default='events/default.jpg')

    def __str__(self):
        return self.name
    
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name