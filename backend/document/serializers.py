import os
from rest_framework import serializers
from .models import Document
from django.db import models
from base.serializers import CategorySerializer


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'category', 'name', 'file', 'size', 'file_type', 'is_hidden']
        # size and file_type are automatically determined
        read_only_fields = ['size', 'file_type']

    def create(self, validated_data):
        # Retrieve the uploaded file instance from validated_data.
        uploaded_file = validated_data.get('file')
        
        # If no name is provided, use the original file name.
        if not validated_data.get('name') and uploaded_file:
            validated_data['name'] = uploaded_file.name
        
        if uploaded_file:
            # Set file size
            validated_data['size'] = uploaded_file.size
            # Determine file_type by extracting the file extension.
            _, ext = os.path.splitext(uploaded_file.name)
            validated_data['file_type'] = ext[1:].lower() if ext else ''
        
        return super().create(validated_data)


class DocumentListSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    class Meta:
        model = Document
        fields = ['id', 'category', 'name', 'file', 'size', 'file_type', 'is_hidden']
        # size and file_type are automatically determined
        read_only_fields = ['size', 'file_type']
