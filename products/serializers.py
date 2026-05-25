from rest_framework import serializers
from .models import Product          # ✅ dot = "from the current app's models.py"

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Product
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']