
from http import HTTPStatus
import logging
from typing import List
from datetime import date
from canvasapi import Canvas

from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import authentication, permissions, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from django.urls import reverse
from rest_framework_tracking.mixins import LoggingMixin
from django_q.tasks import async_task
from django.db.utils import DatabaseError
from backend.canvas_app_explorer.models import ContentItem, CourseScan, CourseScanStatus, ImageItem
from backend import settings
from backend.canvas_app_explorer.canvas_lti_manager.django_factory import DjangoCourseLtiManagerFactory
from backend.canvas_app_explorer.models import CourseScan, CourseScanStatus
from backend.canvas_app_explorer.serializers import ContentQuerySerializer, ReviewContentItemSerializer
from backend.canvas_app_explorer.alt_text_helper.alt_text_update import AltTextUpdate, ContentPayload
from backend.canvas_app_explorer.utils import generate_canvas_content_url

logger = logging.getLogger(__name__)

MANAGER_FACTORY = DjangoCourseLtiManagerFactory(f'https://{settings.CANVAS_OAUTH_CANVAS_DOMAIN}')

class CourseIdRequiredMixin:
    def _require_course_id(self, request: Request) -> int:
        """Return the course ID from the request."""
        course_id = getattr(request, 'course_id')
        return int(course_id)

class AltTextScanViewSet(LoggingMixin, CourseIdRequiredMixin, viewsets.ViewSet):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def start_scan(self, request: Request) -> Response:
        """Create a new course scan record and enqueue the background scan task.

        The task payload includes course, user, and callback context needed by the
        background worker. If task initialization fails after creating a scan row,
        the scan is marked as FAILED before returning an error response.
        """
        course_id = self._require_course_id(request)
        new_course_scan = None

        try:
            new_course_scan = CourseScan.objects.create(
                course_id=int(course_id),
                status=CourseScanStatus.PENDING.value,
            )
            logger.info(f"CourseScan {new_course_scan.id} created for course_id: {course_id}")

            today = date.today().isoformat()
            task_name = f"course_{course_id}_scan_{new_course_scan.id}_on_{today}"

            task_payload = {
                'course_scan_id': new_course_scan.id,
                'course_id': course_id,
                'user_id': request.user.id,
                'canvas_callback_url': request.build_absolute_uri(reverse('canvas-oauth-callback')),
            }

            task_id = async_task(
                'backend.canvas_app_explorer.alt_text_helper.background_tasks.canvas_tools_alt_text_scan.fetch_and_scan_course',
                task=task_payload,
                task_name=task_name
            )
            logger.info(f"Started alt text scan task {task_id} with name '{task_name}' for course_id: {course_id}")

            resp = {
                    'course_id': new_course_scan.course_id,
                    'id': new_course_scan.id,
                    'status': new_course_scan.status,
                }
            return Response(resp, status=HTTPStatus.OK)
        except (DatabaseError, Exception) as e:
            message = f"Failed to initiate course scan due to {e}"
            logger.error(message)

            if new_course_scan is not None:
                new_course_scan.status = CourseScanStatus.FAILED.value
                new_course_scan.save()
                logger.error(f"Marked CourseScan {new_course_scan.id} as FAILED due to exception: {e}")

            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": message})
    
    def get_last_scan(self, request: Request) -> Response:
        course_id = self._require_course_id(request)
        try:
            scan_queryset = CourseScan.objects.filter(course_id=course_id).order_by('-created_at')
            if not scan_queryset.exists():
                logger.info(f"No scan found for course id {course_id} and user {request.user.id}")
                resp = { 'found': False }
                return Response(resp, status=HTTPStatus.OK)
            
            scan_obj = scan_queryset.first()
            scan_detail = {
                    'id': scan_obj.id,
                    'course_id': scan_obj.course_id,
                    'status': scan_obj.status,
                    'created_at': scan_obj.created_at,
                    'updated_at': scan_obj.updated_at,
                    'course_content': self.__get_scan_course_content(scan_obj.id)
                }
            logger.info(f"Returning scan {scan_obj.id} for course id {course_id} and user {request.user.id}")
            resp = {
                'found': True,
                'scan_detail': scan_detail
            }
            return Response(resp, status=HTTPStatus.OK)
        except (DatabaseError, Exception) as e:
            message = f"Failed to retrieve last course scan for course_id {course_id} due to {e}"
            logger.error(message)
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": message})
        
    def __get_scan_course_content(self, course_scan_id: int) -> object:
        try:
            content_by_type = {}
            for content_type,_ in ContentItem.CONTENT_TYPE_CHOICES:
                content_queryset = ContentItem.objects.filter(course_scan_id=course_scan_id, content_type=content_type).all()
                content_by_type[f'{content_type}_list'] = [
                    {
                        'id': content_item.id,
                        'canvas_id': content_item.content_id,
                        'canvas_name': content_item.content_name,
                        'image_count': ImageItem.objects.filter(content_item=content_item).count()
                    }
                    for content_item in content_queryset
                ]
            return content_by_type
        except (Exception) as e:
            logger.error(f"Problem appending course content to scan for course scan id {course_scan_id}")
            raise e

class AltTextContentGetAndUpdateViewSet(LoggingMixin, CourseIdRequiredMixin, viewsets.ViewSet):
    authentication_classes = [authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def _validate_course_ownership(self, validated_data: list, course_id: int, content_types: list) -> Response | None:
        """
        Validate that all content and image IDs belong to the requesting course and content types.
        Returns None if valid, or Response object with 400 error if invalid.
        """
        # Extract content IDs from payload
        content_ids = [item.get('id') for item in validated_data if item.get('id')]
        
        # Extract image IDs from nested images arrays
        image_ids = [
            image.get('image_id')
            for item in validated_data
            for image in item.get('images', [])
        ]
        
        # Verify content items belong to this course and content types
        if content_ids:
            valid_ids = set(
                ContentItem.objects.filter(
                    id__in=content_ids,
                    content_type__in=content_types,
                    course_scan__course_id=course_id
                ).values_list('id', flat=True)
            )
            invalid_ids = set(content_ids) - valid_ids
            if invalid_ids:
                logger.warning(f"Invalid content IDs for course_id {course_id}: {invalid_ids}")
                return Response(
                    status=HTTPStatus.BAD_REQUEST,
                    data={"message": f"Content IDs {invalid_ids} do not belong to this course"}
                )
        
        # Verify image items belong to this course and content types
        if image_ids:
            valid_ids = set(
                ImageItem.objects.filter(
                    id__in=image_ids,
                    content_item__content_type__in=content_types,
                    content_item__course_scan__course_id=course_id
                ).values_list('id', flat=True)
            )
            invalid_ids = set(image_ids) - valid_ids
            if invalid_ids:
                logger.warning(f"Invalid image IDs for course_id {course_id}: {invalid_ids}")
                return Response(
                    status=HTTPStatus.BAD_REQUEST,
                    data={"message": f"Image IDs {invalid_ids} do not belong to this course"}
                )
        
        return None

    @extend_schema(
        parameters=[
            OpenApiParameter(name='content_type', description='Type of content to  like assignment, page, quiz', required=True, type=str),
            OpenApiParameter(name='course_scan_id', description='Course scan ID to scope content lookup', required=True, type=int),
        ],
        request=ContentQuerySerializer,
    )
    def get_content_images(self, request: Request) -> Response:
        request_course_id = self._require_course_id(request)
        # Support both DRF Request (has .query_params) and Django WSGIRequest (has .GET)
        raw_params = getattr(request, 'query_params', request.GET)
        params = raw_params.copy()
        serializer = ContentQuerySerializer(data=params)
        if not serializer.is_valid():
            logger.error("Invalid query parameters for get_content_images: %s", serializer.errors)
            return Response(status=HTTPStatus.BAD_REQUEST, data={"status_code": HTTPStatus.BAD_REQUEST, "message": serializer.errors})

        content_type = serializer.validated_data['content_type']
        course_scan_id = serializer.validated_data.get('course_scan_id')

        if course_scan_id is None:
            logger.error("No scans id sent for request_course_id=%s", request_course_id)
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                data={"status_code": HTTPStatus.BAD_REQUEST, "message": "No course scan Id sent in request" },
            )
        scan_obj = CourseScan.objects.filter(id=course_scan_id).first()
        if scan_obj is None:
            logger.error("Course scan not found for course_scan_id=%s", course_scan_id)
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                data={"status_code": HTTPStatus.BAD_REQUEST, "message": "Invalid course_scan_id"},
            )
        # Keep middleware course context as authority; reject cross-course scan usage.
        if int(scan_obj.course_id) != int(request_course_id):
            logger.error(
                "Course scan mismatch: request_course_id=%s, scan_course_id=%s, course_scan_id=%s",
                request_course_id,
                scan_obj.course_id,
                course_scan_id,
            )
            return Response(
                status=HTTPStatus.BAD_REQUEST,
                data={"status_code": HTTPStatus.BAD_REQUEST, "message": "course_scan_id does not belong to current course"},
            )
        course_id = int(scan_obj.course_id)


        # fetch content items and associated images from DB
        try:
            # include quiz questions when requesting quizzes
            if content_type == ContentItem.CONTENT_TYPE_QUIZ:
                types_to_query = [ContentItem.CONTENT_TYPE_QUIZ, ContentItem.CONTENT_TYPE_QUIZ_QUESTION]
            else:
                types_to_query = [content_type]

            items_qs = ContentItem.objects.filter(
                course_scan_id=course_scan_id,
                content_type__in=types_to_query,
            )
            items_qs = items_qs.prefetch_related('images')
            content_items = []

            # Build a simple map for parent name lookups (parent items are already in items_qs)
            parent_map = {item.content_id: item.content_name for item in items_qs}

            for content_item in items_qs:
                images = []
                for img in content_item.images.all():
                    image_url = img.image_url
                    # Generate Canvas link URL based on content type and IDs
                    canvas_link_url = generate_canvas_content_url(
                        course_id=course_id,
                        content_type=content_item.content_type,
                        content_id=content_item.content_id,
                        content_parent_id=content_item.content_parent_id
                    )
                    images.append({
                        'image_url': image_url,
                        'image_id': img.id,
                        'image_alt_text': img.image_alt_text,
                        'canvas_link_url': canvas_link_url,
                    })

                # Look up parent name if this is a quiz question with a parent
                content_parent_name = None
                if content_item.content_type == ContentItem.CONTENT_TYPE_QUIZ_QUESTION and content_item.content_parent_id:
                    content_parent_name = parent_map.get(content_item.content_parent_id)

                # Set default content_name if missing
                content_name = content_item.content_name or f"Untitled : {content_item.content_type.title()}"

                content_items.append({
                    'id': content_item.id,
                    'content_id': content_item.content_id,
                    'content_name': content_name,
                    'content_parent_id': content_item.content_parent_id,
                    'content_parent_name': content_parent_name,
                    'content_type': content_item.content_type,
                    'images': images,
                })

            resp = {'content_items': content_items}
            return Response(resp, status=HTTPStatus.OK)
        except (DatabaseError, Exception) as e:
            logger.error(f"Failed to fetch content images from DB for course_scan_id {course_scan_id} and content_type {content_type}: {e}")
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"status_code": HTTPStatus.INTERNAL_SERVER_ERROR, "message": str(e)})

    @extend_schema(
        request=ReviewContentItemSerializer
    )
    def alt_text_update(self, request: Request) -> Response:
        course_id = self._require_course_id(request)
        
        serializer = ReviewContentItemSerializer(data=request.data, many=True)
        if not serializer.is_valid():
             return Response(status=HTTPStatus.BAD_REQUEST, data={"message": serializer.errors})

        try:
             # Extract unique content types from the payload
             content_types = list({item.get('content_type') for item in serializer.validated_data if item.get('content_type')})
             
             # Validate that all content and image IDs belong to the requesting course and content types
             validation_error = self._validate_course_ownership(serializer.validated_data, course_id, content_types)
             if validation_error:
                 return validation_error
             logger.info(f"Processing alt text update for course_id {course_id} and content_types {content_types}")
             manager = MANAGER_FACTORY.create_manager(request)
             canvas_api: Canvas = manager.canvas_api
             service = AltTextUpdate(course_id, canvas_api, serializer.validated_data, content_types)
             results_from_alt_text_update: bool|List[ContentPayload] = service.process_alt_text_update()
             
             if results_from_alt_text_update is True:
                logger.info(f"Alt text update completed successfully for course_id {course_id} with content_types {content_types}")
                return Response(status=HTTPStatus.OK)
             else:
                 # Alt text update failed and returned errors; propagate as 500 response
                 logger.error(f"Alt text update failed for course_id {course_id} with content_types {content_types}")
                 return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"message": str(results_from_alt_text_update)})
        except Exception as e:
            logger.error(f"Failed to submit review: {e}")
            return Response(status=HTTPStatus.INTERNAL_SERVER_ERROR, data={"message": str(e)})


