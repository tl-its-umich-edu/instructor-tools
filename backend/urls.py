"""app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.urls import include, path, re_path 
from django.views import static
from rest_framework import routers

from backend.canvas_app_explorer import urls as canvas_app_explorer_urls #type: ignore
from backend.canvas_app_explorer import views as canvas_app_explorer_views #type: ignore

from . import views

# This is for Django Rest Framework
router = routers.DefaultRouter()
router.register(r'lti_tools', canvas_app_explorer_views.LTIToolViewSet, basename='ltitool')
router.register(r'tool_categories', canvas_app_explorer_views.ToolCategoryViewSet, basename='toolcategory')

# Deny all access to the admin login page
admin.site.login = user_passes_test(False, admin.site.login)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('admin/', admin.site.urls),
    path('', views.get_home_template, name = 'home'),

    # These are for the images in the database. When the a new file is uploaded it will have a new name and ID. 
    # extra_headers are passed to cache these files for 1 year which was recommended from 
    #   https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control 
    #   and
    #   https://django-db-file-storage.readthedocs.io/en/stable/#customizing-http-headers

    re_path(r'^files/', include('db_file_storage.urls'), {'extra_headers': {'Cache-Control': 'public, max-age=31536000'}}),
    path('', include(canvas_app_explorer_urls)),
    re_path(r'^status/', include('watchman.urls')),

    # alt text helper endpoints
    path('alt-text-helper/', views.get_home_template, name = 'alt_text_helper'),
    path('api/alt-text/', include('backend.canvas_app_explorer.alt_text_helper.urls')),
]

# This is to aid local development. 
# This exposes the frontend/public directory on a url in static and allows browsing.
# Whitenoise currently handles this otherwise
if settings.DEBUG:
    from django.contrib.staticfiles import views as static_views
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$',
            view = static.serve, 
            kwargs = {
                'document_root': os.path.join(settings.BASE_DIR, 'frontend/public'),
                'show_indexes' : True
            }
        ),
        # Matches STATIC_URL in settings
        re_path(r'^django_static/(?P<path>.*)$', static_views.serve),
        path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
        path('api/schema/swagger-ui', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui')
    ]
