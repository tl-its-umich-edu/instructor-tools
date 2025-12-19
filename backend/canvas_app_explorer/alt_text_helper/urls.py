from django.urls import path
from . import views

urlpatterns = [
    path(
        'scan/<int:course_id>',
        views.AltTextScanViewSet.as_view({
            'post': 'start_scan',
            'get':'get_last_scan'}),
        name='alt_text_start_scan'
    )
]