# llm/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    # path('index/', BuildIndexView.as_view(), name='build-index'),
    # path('', ChatAPIView.as_view(), name='chat'),
    path('conversation/', ConversationListAPIView.as_view(), name='conversations-list'),
    path('conversation/<uuid:conversation_id>/', ConversationDetailAPIView.as_view(), name='conversations-details'),

    path('', ChatIndexView.as_view(), name='chat'),
    path('advanced-augmented-response/', AdvancedAugmentedResponseView.as_view(), name='advanced-augmented-response'),
    # path('index', RecreateIndexView.as_view(), name='recreate-index'),

    path('ai-agent-query/', AIAgentQueryView.as_view(), name='ai-agent-query'),
    path('test-streaming/', TestStreamingView.as_view(), name='test-streaming'),
]
