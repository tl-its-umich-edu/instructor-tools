# Register your models here.

from django.contrib import admin
from backend.canvas_app_explorer.models import LtiTool, CanvasPlacement

@admin.action(description='Make selected lti tools visible to users')
def publish_tool(ltitooladmin, request, queryset):
    queryset.update(is_public=True)

@admin.action(description="Hide selected lti tools from users")
def unpublish_tool(ltitooladmin, request, queryset):
    queryset.update(is_public=False)

class LtiToolAdmin(admin.ModelAdmin):
    fields = (
        'name',
        'canvas_id',
        'is_public',
        ('logo_image', 'logo_image_alt_text'),
        ('main_image', 'main_image_alt_text'),
        'short_description',
        'long_description',
        'privacy_agreement',
        'support_resources',
        'canvas_placement',
        'internal_notes',
    )
    list_display = ('name', 'canvas_id', 'is_public')
    actions = [publish_tool, unpublish_tool]


admin.site.register(LtiTool, LtiToolAdmin)


class CanvasPlacementAdmin(admin.ModelAdmin):
    pass


admin.site.register(CanvasPlacement, CanvasPlacementAdmin) 
