from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Application
from .serializers import ApplicationListSerializer, ApplicationDetailSerializer, ApplicationCreateSerializer
from .permissions import CanEditDraft
from apps.applications.services.workflow import WorkflowService, IllegalTransition, TransitionPermissionDenied, WorkflowError
from apps.audits.models import AuditLog


def error_response(code: str, message: str, details=None, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({'error': {'code': code, 'message': message, 'details': details}}, status=http_status)


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all().select_related('owner')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationListSerializer
        if self.action in ('create',):
            return ApplicationCreateSerializer
        return ApplicationDetailSerializer

    def get_permissions(self):
        perms = [p() for p in self.permission_classes]
        if self.action in ('partial_update', 'update'):
            perms.append(CanEditDraft())
        return perms

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.groups.filter(name='reviewer').exists():
            return super().get_queryset()
        return super().get_queryset().filter(owner=user)

    @action(detail=True, methods=['post'], url_path='transitions')
    def transitions(self, request, pk=None):
        app = get_object_or_404(Application, pk=pk)
        target = request.data.get('target')
        comment = request.data.get('comment')
        metadata = request.data.get('metadata')
        try:
            updated = WorkflowService.transition(application=app, actor=request.user, target_status=target, comment=comment, metadata=metadata)
        except IllegalTransition as e:
            return error_response('illegal_transition', str(e), http_status=status.HTTP_400_BAD_REQUEST)
        except TransitionPermissionDenied as e:
            return error_response('permission_denied', str(e), http_status=status.HTTP_403_FORBIDDEN)
        except WorkflowError as e:
            return error_response('workflow_error', str(e), http_status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response('server_error', 'internal server error', details=str(e), http_status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = ApplicationDetailSerializer(updated, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='audit')
    def audit(self, request, pk=None):
        app = get_object_or_404(Application, pk=pk)
        qs = AuditLog.objects.filter(application_id=app.id).order_by('-created_at')
        data = [{'id': a.id, 'from': a.from_status, 'to': a.to_status, 'comment': a.comment, 'actor': a.actor_id, 'created_at': a.created_at} for a in qs]
        return Response(data)
