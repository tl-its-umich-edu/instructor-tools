
from typing import List

from django.contrib.auth.models import User
from rest_framework import fields, serializers

from backend.canvas_app_explorer import models
from backend.canvas_app_explorer.canvas_lti_manager.data_class import ExternalToolTab
from backend.canvas_app_explorer.models import ContentItem


class GlobalsUserSerializer(serializers.ModelSerializer):
    """
    Basic serializer for User model for sharing basic attributes with the UI as globals
    """

    class Meta:
        model = User
        fields = ['username', 'is_staff']


class CanvasPlacementSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.CanvasPlacement
        fields = '__all__'

class ToolCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.ToolCategory
        fields = '__all__'


class LtiToolSerializer(serializers.ModelSerializer):
    """
    Serializer for LtiTool model, with nested CanvasPlacements
    """
    canvas_placement_expanded = CanvasPlacementSerializer(read_only=True, many=True, source='canvas_placement')
    tool_categories_expanded = ToolCategorySerializer(read_only=True, many=True, source='tool_categories')

    class Meta:
        model = models.LtiTool
        fields = [
            'id', 'name', 'canvas_id', 'logo_image', 'logo_image_alt_text', 'main_image',
            'main_image_alt_text', 'short_description', 'long_description', 'privacy_agreement',
            'support_resources', 'canvas_placement_expanded', 'tool_categories_expanded', 'launch_url',
        ]


class LtiToolWithNavSerializer(LtiToolSerializer):
    """
    Serializer extending LtiToolSerializer with additional navigation data specific to a course context
    """
    navigation_enabled = serializers.SerializerMethodField()

    def get_navigation_enabled(self, obj: models.LtiTool) -> bool:
        """
        Matching serializer method for navigation_enabled field that finds the expected tool data and
        returns the navigation status
        """
        if 'available_tools' not in self.context:
            raise Exception('"available_tools" must be passed to the LtiToolSerializer context.')
        available_tools = self.context['available_tools']
        # Search in tools available in the context for a canvas ID matching the model instance
        matches: List[ExternalToolTab] = list(filter(lambda x: x.id == obj.canvas_id, available_tools))
        # For LTI tools (null for launch_url), if there is exactly one match, return its navigation status
        if obj.launch_url is None:
            if len(matches) == 1:
                first_match = matches[0] # Canvas IDs should be unique
                return not first_match.is_hidden
            raise Exception(
                'Expected exactly one match for available tool data from Canvas; '
                f'{len(matches)} were found.'
            )

    class Meta(LtiToolSerializer.Meta):
        fields = LtiToolSerializer.Meta.fields + ['navigation_enabled']


class UpdateLtiToolNavigationSerializer(serializers.Serializer):
    """
    Serializer for body data expected when updating a tool's navigation status in a course context
    """
    navigation_enabled = fields.BooleanField()

class ContentQuerySerializer(serializers.Serializer):
    content_type = serializers.ChoiceField(
        choices=ContentItem.CONTENT_TYPE_CHOICES
    )

class ReviewImageItemSerializer(serializers.Serializer):
    image_id = serializers.IntegerField(required=True)
    action = serializers.ChoiceField(choices=['approve', 'skip'], required=True)
    approved_alt_text = serializers.CharField(allow_blank=True, required=False)

class ReviewContentItemSerializer(serializers.Serializer):
    content_id = serializers.IntegerField(required=False)
    content_type = serializers.ChoiceField(choices=ContentItem.CONTENT_TYPE_CHOICES, required=False)
    images = ReviewImageItemSerializer(many=True)
