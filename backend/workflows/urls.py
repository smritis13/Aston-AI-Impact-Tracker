from . import views
from django.urls import path, include

urlpatterns = [
    path('', views.WorkflowDefinitionListCreateView.as_view(), name='workflow-list-create'),
    path('<uuid:pk>/', views.WorkflowDefinitionDetailView.as_view(), name='workflow-detail'),
    path('agent/', views.AgentListCreateView.as_view(), name='agent-list-create'),
    path('agent/<uuid:pk>/', views.AgentDetailView.as_view(), name='agent-detail'),
    path('executions/', views.WorkflowExecutionListCreateView.as_view(), name='execution-list-create'),
    path('executions/<uuid:pk>/', views.WorkflowExecutionDetailView.as_view(), name='execution-detail'),
    path('tools/', views.AvailableToolsView.as_view(), name='available-tools'),
    path('tool-configs/', views.ToolConfigListCreateView.as_view(), name='tool-config-list-create'),
    path('tool-configs/<uuid:pk>/', views.ToolConfigDetailView.as_view(), name='tool-config-detail'),
    
    path('tavily-test/', views.TavilySearchTestView.as_view(), name='tavily-test'),
]