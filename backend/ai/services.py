"""AI services: job execution (mock generation) with mandatory human review."""
from django.utils import timezone

from . import models


def run_job(job):
    """Execute an AI job synchronously, producing GeneratedContent in PENDING_REVIEW.

    Real provider integration is out of scope; this generates a placeholder so the
    human-review gate can be exercised end-to-end.
    """
    job.status = models.AIJob.Status.RUNNING
    job.save(update_fields=["status", "updated_at"])

    input_data = job.input or {}
    prompt = input_data.get("prompt", "")
    content_type = input_data.get("content_type", models.GeneratedContent.ContentType.MATERIAL)
    title = input_data.get("title", f"Generated {job.get_job_type_display()}")

    body = (
        f"[AI-generated draft]\n\nPrompt: {prompt}\n\n"
        "This content requires human review before publication."
    )

    content = models.GeneratedContent.objects.create(
        institution_id=job.institution_id,
        job=job,
        content_type=content_type,
        title=title,
        body=body,
        status=models.GeneratedContent.Status.PENDING_REVIEW,
    )

    job.status = models.AIJob.Status.SUCCESS
    job.output = {"generated_content_id": content.id}
    job.save(update_fields=["status", "output", "updated_at"])
    return content
