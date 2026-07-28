
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def api_root(request):
    """API root endpoint showing available routes"""
    return JsonResponse({
        'message': 'Aston AI Research Tool API',
        'version': '1.0',
        'endpoints': {
            'admin': '/admin/',
            'base': '/base/',
            'chat': '/chat/',
            'auth': '/auth/',
            'document': '/document/',
            'content': '/content/',
            'agent': '/agent/',
            'workflow': '/workflow/',
        },
        'frontend': 'http://localhost:3001',
        'api_docs': 'Visit /admin/ for Django admin interface'
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('base/', include('base.urls')),
    path('chat/', include('chat.urls')),
    path('auth/', include('authapp.urls')),
    path('document/', include('document.urls')),
    path('content/', include('content.urls')),
    path('agent/', include('agent.urls')),
    path('workflow/', include('workflows.urls')),
]
