from rest_framework import viewsets
from core.models import AutoPart
from inventory import serializers

class AutoPartView(viewsets.ModelViewSet):
    serializer_class = serializers.AutoPartSerializer
    queryset = AutoPart.objects.all()
