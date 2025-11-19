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
    canvas_placement = models.ManyToManyField(CanvasPlacement)
    internal_notes = HTMLField(blank=True, null=True, help_text="a place to put helpful info for admins, not visible to users")
    launch_url = models.CharField(max_length=2048, blank=True, null=True, help_text="A link that will directly be launched by clicking on this card. If this is value is set then canvas_id is ignored")

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

# New model: track course scan tasks
class CourseScan(models.Model):
    # Big primary key
    id = models.BigAutoField(primary_key=True)
    # Canvas course id (use BigInteger in case of large values)
    canvas_id = models.BigIntegerField(db_index=True, unique=True)
    # ID returned by the scan task system (e.g. django-q task id)
    scan_task_id = models.CharField(max_length=255, blank=True, null=True)
    # Simple status string (pending, running, completed, failed, etc.)
    status = models.CharField(max_length=50, default='pending', db_index=True)
    # When the scan was created
    created_at = models.DateTimeField(auto_now_add=True)
    # When the scan was last updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'canvas_app_explorer_course_scan'
        ordering = ['-created_at']

    def __str__(self):
        return f"CourseScan(id={self.id}, canvas_id={self.canvas_id}, status={self.status})"


class ImageItem(models.Model):
    CONTENT_TYPE_ASSIGNMENT = 'assignment'
    CONTENT_TYPE_PAGE = 'page'
    CONTENT_TYPE_CHOICES = (
        (CONTENT_TYPE_ASSIGNMENT, 'Assignment'),
        (CONTENT_TYPE_PAGE, 'Page'),
    )

    id = models.BigAutoField(primary_key=True)
    # ForeignKey to CourseScan using its `canvas_id` field so ImageItem is tied to the course
    course_scan = models.ForeignKey(
        CourseScan,
        to_field='canvas_id',
        on_delete=models.CASCADE,
        db_column='canvas_id',
        related_name='image_items',
    )
    image_content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    image_id = models.BigIntegerField()
    image_url = models.URLField(max_length=2048)
    # If the content is an assignment this is assignment_id; if page then page_id
    image_content_id = models.BigIntegerField()

    class Meta:
        db_table = 'canvas_app_explorer_image_item'

    def __str__(self):
        return f"ImageItem(id={self.id}, canvas_id={self.course_scan_id}, type={self.image_content_type}, image_id={self.image_id})"
