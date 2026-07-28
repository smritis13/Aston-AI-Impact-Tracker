from rest_framework import serializers
from .models import Category



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'parent']

class CategoryListSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'subcategories']

    def get_subcategories(self, obj):
        children = Category.objects.filter(parent=obj)
        return CategoryListSerializer(children, many=True).data  # Recursively serialize subcategories
