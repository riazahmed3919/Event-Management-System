from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Event
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.db.models.signals import post_save

@receiver(m2m_changed, sender=Event.participants.through)
def send_rsvp_email_signal(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        for user_id in pk_set:
            user = User.objects.get(pk=user_id)
            subject = f"RSVP Confirmation for {instance.name}"
            message = (
                f"Hi {user.first_name or user.username},\n\n"
                f"You have successfully RSVPed for the event '{instance.name}'.\n"
                f"Date: {instance.date}\n"
                f"Time: {instance.time}\n"
                f"Location: {instance.location}\n\n"
                f"Thank you for your interest!"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

@receiver(post_save, sender=User)
def send_activation_email_signal(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)
        activation_link = f"{settings.FRONTEND_URL}{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"

        subject = "Activate your account"

        message = f"""
        Hi {instance.first_name or instance.username},

        Thank you for registering!

        Please click the link below to activate your account:
        {activation_link}

        If you did not sign up, please ignore this email.

        Best regards,
        Your Team
        """

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=False,
        )