"""Academics signals.

Enforce the "single active" invariants at the model layer so that no code path
(API, admin, management command, shell) can leave two active years/terms.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AcademicYear, Term


@receiver(post_save, sender=AcademicYear)
def deactivate_other_academic_years(sender, instance, created, **kwargs):
    """Keep at most one active AcademicYear per institution."""
    if not instance.is_active:
        return
    AcademicYear.all_objects.filter(
        institution_id=instance.institution_id, is_active=True
    ).exclude(pk=instance.pk).update(is_active=False)


@receiver(post_save, sender=Term)
def deactivate_other_terms(sender, instance, created, **kwargs):
    """Keep at most one active Term per AcademicYear."""
    if not instance.is_active:
        return
    Term.all_objects.filter(
        academic_year_id=instance.academic_year_id, is_active=True
    ).exclude(pk=instance.pk).update(is_active=False)
