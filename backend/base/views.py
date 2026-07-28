from rest_framework import generics
from .models import Category
from .serializers import *

# List all categories or create a new one
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if(self.request.method == 'POST'):
            return CategorySerializer
        else:
            return CategoryListSerializer

# Retrieve, update, or delete a specific category
class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = [IsAuthenticated]
