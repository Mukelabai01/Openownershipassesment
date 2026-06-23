import uuid
from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application_id = models.UUIDField()  # denormalized reference for portability
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    from_status = models.CharField(max_length=32, null=True, blank=True)
    to_status = models.CharField(max_length=32)
    comment = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['application_id', 'created_at'])]

    def __str__(self) -> str:
        return f"AuditLog({self.application_id} {self.from_status}->{self.to_status})"
