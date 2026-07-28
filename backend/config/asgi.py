"""
ASGI config for config project.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import re_path
from core.llm.utils.consumers import StreamConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Define WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'ws/stream/(?P<report_id>\d+)/(?P<stream_id>[0-9a-f-]{36})/(?P<channel_type>[^/]+)/$', StreamConsumer.as_asgi()),
    re_path(r'ws/stream/(?P<stream_id>[0-9a-f-]{36})/(?P<channel_type>[^/]+)/$', StreamConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})