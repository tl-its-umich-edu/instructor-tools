from django.urls import path
from . import views

urlpatterns = [
    # temporary endpoint to test background task
    path(
        'scan/',
        views.AltTextScanViewSet.as_view({'post': 'start_scan'}),
        name='alt_text_start_scan'
    ),
    path(
        'content-images/course/<str:course_id>',
        views.AltTextGetContentImagesViewSet.as_view({'get': 'get_content_images'}),
        name='alt_text_get_content_images'
    ),
]