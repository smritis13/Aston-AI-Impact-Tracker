from django.urls import path
from .views import *

urlpatterns = [
    # File Endpoints
    path('', DocumentListCreateView.as_view(), name='document-list-create'),
    path('<int:pk>/', DocumentDetailView.as_view(), name='document-detail'),

]
