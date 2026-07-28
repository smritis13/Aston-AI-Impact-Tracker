# llm/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('workflow/', WorkflowListCreateView.as_view(), name='workflow-list-create'),
    path('workflow/<int:pk>/', WorkflowDetailView.as_view(), name='workflow-detail'),
    path('node/', NodeListCreateView.as_view(), name='node-list-create'),
    path('node/<int:pk>/', NodeDetailView.as_view(), name='node-detail'),
    path('edge/', EdgeListCreateView.as_view(), name='edge-list-create'),
    path('edge/<int:pk>/', EdgeDetailView.as_view(), name='edge-detail'),
    path('workflow/<int:workflow_id>/execute/', ExecuteWorkflowView.as_view(), name='workflow-execute'),
   
]
