# Register your models here.

from django.contrib import admin
from backend.canvas_app_explorer.models import LtiTool, CanvasPlacement, ToolCategory, CourseScan

@admin.register(LtiTool)
class LtiToolAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'canvas_id',
        'launch_url',
        ('logo_image', 'logo_image_alt_text'),
        ('main_image', 'main_image_alt_text'),
        'short_description',
        'long_description',
        'privacy_agreement',
        'support_resources',
        'canvas_placement',
        'tool_categories',
        'internal_notes',
    )
    list_display = ('name', 'canvas_id')




@admin.register(CanvasPlacement)
class CanvasPlacementAdmin(admin.ModelAdmin):
    pass



@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(CourseScan)
class CourseScanAdmin(admin.ModelAdmin):
    list_display = ('id', 'course_id', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('course_id', 'q_task_id')
    readonly_fields = ('course_id', 'q_task_id', 'id', 'created_at', 'updated_at')

