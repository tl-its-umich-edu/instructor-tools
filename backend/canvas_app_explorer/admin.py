# Register your models here.

from django.contrib import admin
from backend.canvas_app_explorer.models import LtiTool, CanvasPlacement, ToolCategory

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


admin.site.register(LtiTool, LtiToolAdmin)


class CanvasPlacementAdmin(admin.ModelAdmin):
    pass


admin.site.register(CanvasPlacement, CanvasPlacementAdmin) 

class ToolCategoryAdmin(admin.ModelAdmin):
    pass
admin.site.register(ToolCategory, ToolCategoryAdmin)
