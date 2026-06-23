from typing import Optional
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.applications.models import Application
from apps.audits.models import AuditLog

User = get_user_model()


class WorkflowError(Exception):
    pass


class IllegalTransition(WorkflowError):
    pass


class TransitionPermissionDenied(WorkflowError):
    pass


ALLOWED_TRANSITIONS = {
    Application.Status.DRAFT: [Application.Status.SUBMITTED],
    Application.Status.SUBMITTED: [Application.Status.UNDER_REVIEW],
    Application.Status.UNDER_REVIEW: [Application.Status.APPROVED, Application.Status.REJECTED, Application.Status.DRAFT],
}


def is_reviewer(user: User) -> bool:
    if user is None or not user.is_authenticated:
        return False
    return user.is_staff or user.groups.filter(name='reviewer').exists()


class WorkflowService:
    @staticmethod
    def transition(application: Application, actor: User, target_status: str, comment: Optional[str] = None, metadata: Optional[dict] = None) -> Application:
        if metadata is None:
            metadata = {}

        with transaction.atomic():
            app = Application.objects.select_for_update().get(pk=application.pk)
            current = app.status

            allowed = ALLOWED_TRANSITIONS.get(current, [])
            if target_status not in allowed:
                raise IllegalTransition(f'Illegal transition {current} -> {target_status} is not allowed')

            if current == Application.Status.DRAFT and target_status == Application.Status.SUBMITTED:
                if actor != app.owner:
                    raise TransitionPermissionDenied('Only the owner may submit a draft')

            if current in (Application.Status.SUBMITTED, Application.Status.UNDER_REVIEW):
                if not is_reviewer(actor):
                    raise TransitionPermissionDenied('Only a reviewer may change status from SUBMITTED or UNDER_REVIEW')

            if target_status in (Application.Status.REJECTED, Application.Status.DRAFT) and not comment:
                raise WorkflowError('Comment is required for reject or return-for-changes transitions')

            from_status = app.status
            app.status = target_status
            if target_status == Application.Status.SUBMITTED:
                app.submitted_at = timezone.now()
            app.save(update_fields=['status', 'submitted_at', 'updated_at'])

            AuditLog.objects.create(application_id=app.id, actor=actor, from_status=from_status, to_status=target_status, comment=comment or '', metadata=metadata or {})

            return app
