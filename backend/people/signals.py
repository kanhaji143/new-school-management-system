"""People signals.

Guarantees that every student / teacher / guardian has the matching portal role,
regardless of whether the record was created through the API, the Django admin
or a management command.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import services
from .models import Guardian, Student, Teacher


@receiver(post_save, sender=Student)
def assign_student_role(sender, instance, created, **kwargs):
    if created:
        services.assign_role(instance.user, services.STUDENT_ROLE)


@receiver(post_save, sender=Teacher)
def assign_teacher_role(sender, instance, created, **kwargs):
    if created:
        services.assign_role(instance.user, services.TEACHER_ROLE)


@receiver(post_save, sender=Guardian)
def assign_guardian_role(sender, instance, created, **kwargs):
    if created:
        services.assign_role(instance.user, services.PARENT_ROLE)
