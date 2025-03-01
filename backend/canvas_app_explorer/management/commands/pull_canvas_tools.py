from django.core.management.base import BaseCommand, CommandParser
from canvasapi import Canvas

from backend.canvas_app_explorer.models import LtiTool, CanvasPlacement

# register customized actions with manage.py
# usage: python manage.py pull (<num_tools_retrived>?) <API_KEY> (<API_URL>) 
class Command(BaseCommand):
    help = "pull info about available external tools on Canvas to populate a local database"

    def add_arguments(self, parser):
        parser.add_argument('api_key', nargs=1, type=str)
        parser.add_argument('api_url', nargs='?', type=str, default="https://umich-dev.instructure.com")

    def handle(self, *args, **options):
        
        API_KEY = options['api_key'][0]
        API_URL = options['api_url']
        canvas = Canvas(API_URL, API_KEY)

        primary_acount = canvas.get_account(1)
        ex_tool_list = primary_acount.get_external_tools()
        # for ManyToManyField setup
        course_nav_placement = CanvasPlacement.objects.get(name='Course Navigation')
        for ex_tool in ex_tool_list:
            # for now, only care about tools with placement "course_navigation"
            if ex_tool.__dict__["course_navigation"] is not None \
                and ex_tool.__dict__["course_navigation"]["enabled"] == True:

                # avoid duplicates: get_or_create
                if not LtiTool.objects.filter(canvas_id=ex_tool.id).exists():
                    tool = LtiTool.objects.create(
                        name=ex_tool.name, 
                        canvas_id=ex_tool.id, 
                        # HTMLFields without blank=True need placeholder strings
                        short_description="",
                        long_description="",
                        privacy_agreement="",
                        support_resources="",
                    )
                    tool.canvas_placement.add(course_nav_placement)