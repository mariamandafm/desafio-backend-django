from rest_framework import viewsets, permissions
from core.models import AutoPart
from inventory import serializers


class AutoPartView(viewsets.ModelViewSet):
    serializer_class = serializers.AutoPartSerializer
    queryset = AutoPart.objects.all()

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]

        return [permission() for permission in permission_classes]
