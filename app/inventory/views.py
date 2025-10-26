from rest_framework import viewsets, permissions
from core.models import AutoPart
from inventory import serializers

class OnlyAdminPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_staff
    

class AutoPartView(viewsets.ModelViewSet):
    serializer_class = serializers.AutoPartSerializer
    queryset = AutoPart.objects.all()
    permission_classes = [OnlyAdminPermissions]
