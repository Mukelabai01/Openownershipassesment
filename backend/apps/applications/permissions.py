from rest_framework import permissions
from .models import Application


class CanEditDraft(permissions.BasePermission):
    def has_object_permission(self, request, view, obj: Application):
        if obj.status != Application.Status.DRAFT:
            return False
        return obj.owner_id == request.user.id


class IsReviewer(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.groups.filter(name='reviewer').exists()))
