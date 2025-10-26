from rest_framework import serializers
from core.models import AutoPart


class AutoPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoPart
        fields = ['id', 'name', 'description', 'price', 'stock_quantity']
