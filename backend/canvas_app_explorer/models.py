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
    is_public = models.BooleanField(default=False, help_text="true if the tool is visible to users")

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
