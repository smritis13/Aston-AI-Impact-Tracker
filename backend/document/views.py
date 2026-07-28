from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from .models import *
from .serializers import *
from core.permissions import IsEditor, IsAdmin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from base.pagination import CustomPagination
from core.llm.text_extract import TextExtractor
from rest_framework.views import APIView


# Document Views
class DocumentListCreateView(generics.ListCreateAPIView):
    queryset = Document.objects.all().order_by('sort_order')
    serializer_class = DocumentSerializer
    pagination_class = CustomPagination
    # permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if(self.request.method == 'GET'):
            return DocumentListSerializer
        else:
            return DocumentSerializer
    
    def get_queryset(self):
        """
        Override this method to allow filtering by category and search query.
        """
        queryset = Document.objects.all().order_by('sort_order')

        # Get query parameters
        category_id = self.request.query_params.get('category')
        search_query = self.request.query_params.get('query', '').strip()

        # Filter by category if provided
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by search query in document name
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(file_type__icontains=search_query))

        return queryset
    
    def perform_create(self, serializer):
        # Save the Document object so we have the actual file on disk
        document = serializer.save()

        # Extract text and store it in the model
        if document.file and document.file_type:
            extracted_text = TextExtractor.extract(document.file.path, document.file_type)
            extracted_text = extracted_text.encode('utf-8', 'ignore').decode('utf-8')
            document.content = extracted_text
            document.save()

class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    # permission_classes = [IsAuthenticated]


