"""Helpers for writing append-only audit records."""
from audit.models import AuditLog


def log_action(actor, action, instance=None, before=None, after=None, *, ip_address=None,
               user_agent=None, institution_id=None):
    """
    Record a change. Safe to call from signals/services.

    `before` / `after` are JSON-serialisable dicts of the object state.
    """
    if instance is not None:
        institution_id = institution_id or getattr(instance, "institution_id", None)
        model = instance.__class__._meta.label
        object_id = getattr(instance, "pk", None)
        object_repr = str(instance)[:200]
    else:
        model = object_id = object_repr = ""

    return AuditLog.all_objects.create(
        institution_id=institution_id,
        actor=actor,
        action=action,
        model=model,
        object_id=object_id,
        object_repr=object_repr,
        before=before or {},
        after=after or {},
        ip_address=ip_address,
        user_agent=user_agent or "",
    )


def instance_to_dict(instance, fields=None):
    """Snapshot a model instance into a JSON-friendly dict."""
    fields = fields or [f.name for f in instance._meta.fields]
    data = {}
    for name in fields:
        value = getattr(instance, name, None)
        if hasattr(value, "pk"):  # related object
            value = value.pk
        data[name] = value
    return data
