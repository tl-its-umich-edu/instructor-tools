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

class CourseScan(models.Model):
    # Big primary key
    id = models.BigAutoField(primary_key=True)
    # Course id (use BigInteger in case of large values)
    course_id = models.BigIntegerField(unique=True)
    # ID returned by the scan task system (e.g. django-q task id)
    q_task_id = models.CharField(max_length=255, blank=True, null=True)
    # Simple status string (pending, running, completed, failed)
    status = models.CharField(max_length=50, default='pending')
    # When the scan was created
    created_at = models.DateTimeField(auto_now_add=True)
    # When the scan was last updated
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'canvas_app_explorer_course_scan'
        ordering = ['-created_at']

    def __str__(self):
        return f"CourseScan(id={self.id}, course_id={self.course_id}, q_task_id={self.q_task_id}, status={self.status})"

class CourseScanStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    FAILED = "failed", "Failed"
    COMPLETED = "completed", "Completed"



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
    # FK to CourseScan (stored in DB column `course_id`)
    course = models.ForeignKey(
        CourseScan,
        to_field='course_id',
        on_delete=models.CASCADE,
        db_column='course_id',
        related_name='content_items',
    )
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    content_id = models.BigIntegerField(unique=True)
    content_name = models.CharField(max_length=255, null=True, blank=True)
    # for quiz question
    content_parent_id = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'canvas_app_explorer_content_item'

    def __str__(self):
        return f"ContentItem(id={self.id}, course_id={self.course_id}, type={self.content_type}, content_name={self.content_name}, content_parent_id={self.content_parent_id})"


class ImageItem(models.Model):
    id = models.BigAutoField(primary_key=True)
    # FK to CourseScan using DB column `course_id`
    course = models.ForeignKey(
        CourseScan,
        to_field='course_id',
        on_delete=models.CASCADE,
        db_column='course_id',
        related_name='image_items',
    )
    # FK to ContentItem (stored in DB column `content_id`)
    content_item = models.ForeignKey(
        'ContentItem',
        to_field='content_id',
        on_delete=models.CASCADE,
        db_column='content_id',
        related_name='images',
    )
    image_id = models.BigIntegerField(null=True, blank=True)
    image_url = models.URLField(max_length=2048)
    # optional alt text produced by AI or provided by user; limit to ~2000 characters
    image_alt_text = models.TextField(blank=True, null=True, validators=[MaxLengthValidator(2000)])

    class Meta:
        db_table = 'canvas_app_explorer_image_item'

    def __str__(self):
        return f"ImageItem(id={self.id}, course_id={self.course_id}, content_item_id={self.content_item_id}, image_id={self.image_id})"
