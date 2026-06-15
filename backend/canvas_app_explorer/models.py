from django.core.validators import MaxLengthValidator
from django.db import models
from django.utils.deconstruct import deconstructible
from django.utils.html import strip_tags
from db_file_storage.model_utils import delete_file, delete_file_if_needed
from tinymce.models import HTMLField

# Validator that checks the length but ignores HTML tags
# Use in your model as validators=[MaxLengthIgnoreHTMLValidator(limit_value=120)]
@deconstructible
class MaxLengthIgnoreHTMLValidator(MaxLengthValidator):
    def clean (self, value: str):
        return len(strip_tags(value))

class CanvasPlacement(models.Model):
    name = models.CharField(max_length=150)
    def __str__(self):
        return self.name

class ToolCategory(models.Model):
    category_name = models.CharField(max_length=150)
    def __str__(self):
        return self.category_name
    class Meta:
        verbose_name = "Tool Category"
        verbose_name_plural = "Tool Categories"
class LogoImage(models.Model):
    bytes = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=50)

class MainImage(models.Model):
    bytes = models.TextField()
    filename = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=50)

class LtiTool(models.Model):
    name = models.CharField(max_length=50)
    canvas_id = models.IntegerField(unique=True, blank=True, null=True)
    logo_image = models.ImageField(upload_to='canvas_app_explorer.LogoImage/bytes/filename/mimetype', blank=True, null=True)
    logo_image_alt_text = models.CharField(max_length=255, blank=True, null=True)
    main_image = models.ImageField(upload_to='canvas_app_explorer.MainImage/bytes/filename/mimetype', blank=True, null=True)
    main_image_alt_text = models.CharField(max_length=255, blank=True, null=True)
    short_description = HTMLField(validators=[MaxLengthIgnoreHTMLValidator(limit_value=120)])
    long_description = HTMLField()
    privacy_agreement = HTMLField()
    support_resources = HTMLField()
    canvas_placement = models.ManyToManyField(CanvasPlacement, blank=True)
    internal_notes = HTMLField(blank=True, null=True, help_text="a place to put helpful info for admins, not visible to users")
    launch_url = models.CharField(max_length=2048, blank=True, null=True, help_text="A link that will directly be launched by clicking on this card. If this is value is set then canvas_id is ignored")
    tool_categories = models.ManyToManyField(ToolCategory, blank=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        delete_file_if_needed(self, 'logo_image')
        delete_file_if_needed(self, 'main_image')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        delete_file_if_needed(self, 'logo_image')
        delete_file_if_needed(self, 'main_image')

class CourseScanStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    FAILED = "failed", "Failed"
    COMPLETED = "completed", "Completed"


class CourseScan(models.Model):
    # Big primary key
    id = models.BigAutoField(primary_key=True)
    # Course id (use BigInteger in case of large values)
    course_id = models.BigIntegerField()
    # Simple status string (pending, running, completed, failed)
    status = models.CharField(max_length=50, default=CourseScanStatus.PENDING, choices=CourseScanStatus.choices)
    # Total number of images found in the course scan (defaults to 0 for previous scans)
    total_image_count = models.IntegerField(default=0)
    # When the scan was created
    created_at = models.DateTimeField(auto_now_add=True)
    # When the scan was last updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'canvas_app_explorer_course_scan'
        ordering = ['-created_at']

    def __str__(self):
        return f"CourseScan(id={self.id}, course_id={self.course_id}, status={self.status})"



class ContentItem(models.Model):
    CONTENT_TYPE_ASSIGNMENT = 'assignment'
    CONTENT_TYPE_PAGE = 'page'
    CONTENT_TYPE_QUIZ = 'quiz'
    CONTENT_TYPE_QUIZ_QUESTION = 'quiz_question'
    CONTENT_TYPE_CHOICES = (
        (CONTENT_TYPE_ASSIGNMENT, 'Assignment'),
        (CONTENT_TYPE_PAGE, 'Page'),
        (CONTENT_TYPE_QUIZ, 'Quiz'),
        (CONTENT_TYPE_QUIZ_QUESTION, 'Quiz Question'),
    )

    id = models.BigAutoField(primary_key=True)
    # FK to CourseScan primary key
    course_scan = models.ForeignKey(
        CourseScan,
        on_delete=models.CASCADE,
        db_column='course_scan_id',
        related_name='content_items',
    )
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.BigIntegerField()
    content_name = models.CharField(max_length=255, null=True, blank=True)
    # for quiz question
    content_parent_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'canvas_app_explorer_content_item'
        constraints = [
            models.UniqueConstraint(fields=['course_scan', 'content_id'], name='uniq_contentitem_scan_content_id'),
        ]

    def __str__(self):
        return f"ContentItem(id={self.id}, course_scan_id={self.course_scan_id}, type={self.content_type}, content_name={self.content_name}, content_parent_id={self.content_parent_id})"


class ImageItem(models.Model):
    IMAGE_STATE_PENDING = 'pending'
    IMAGE_STATE_SUCCESS = 'success'
    IMAGE_STATE_FAILED = 'failed'
    IMAGE_STATE_CHOICES = [
        (IMAGE_STATE_PENDING, 'Pending'),
        (IMAGE_STATE_SUCCESS, 'Success'),
        (IMAGE_STATE_FAILED, 'Failed'),
    ]

    id = models.BigAutoField(primary_key=True)
    # FK to ContentItem primary key
    content_item = models.ForeignKey(
        ContentItem,
        on_delete=models.CASCADE,
        db_column='content_item_id',
        related_name='images',
    )
    image_url = models.URLField(max_length=2048)
    # optional alt text produced by AI or provided by user; limit to ~2000 characters
    image_alt_text = models.TextField(blank=True, null=True, validators=[MaxLengthValidator(2000)])
    # Tracks image processing lifecycle. Failed items are excluded from review payloads.
    image_process_state = models.CharField(
        max_length=20,
        choices=IMAGE_STATE_CHOICES,
        default=IMAGE_STATE_PENDING,
    )

    class Meta:
        db_table = 'canvas_app_explorer_image_item'

    def __str__(self):
        return f"ImageItem(id={self.id})"


class CourseScanErrorLog(models.Model):
    """
    Stores errors that occur during a course scan.
    
    Related to CourseScan via FK, capturing error details including:
    - Error type (assignment | page | quiz | question | quiz_question | image_process_error | alt_text_process_error | 
        token_error | content_database_save | course_scan_update_error
    - title = Content title if related to specific content item, otherwise 'Course' or other relevant descriptor
    - Exception message/traceback
    - Canvas UI URL pointing to the failing content/course
    """
    id = models.BigAutoField(primary_key=True)
    
    course_scan = models.ForeignKey(
        CourseScan,
        on_delete=models.CASCADE,
        db_column='course_scan_id',
        related_name='scan_errors',
    )
    
    error_type = models.CharField(max_length=50)

    error_title = models.CharField(max_length=255, blank=True, null=True)
    
    error_message = models.TextField()
    
    canvas_url = models.URLField(max_length=2048, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'canvas_app_explorer_course_scan_error_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course_scan', '-created_at']),
        ]

    def __str__(self):
        return f"CourseScanErrorLog(id={self.id}, course_scan_id={self.course_scan_id}, type={self.error_type})"
