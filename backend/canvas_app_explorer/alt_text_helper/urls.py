from django.urls import path
from . import views

urlpatterns = [
    path(
        'scan',
        views.AltTextScanViewSet.as_view({
            'post': 'start_scan',
            'get':'get_last_scan'}),
        name='alt_text_start_scan'
    ),
    path(
        'content-images',
        views.AltTextContentGetAndUpdateViewSet.as_view({
            'get': 'get_content_images'}),
        name='alt_text_get_content_images'
    ),
]