DEFAUlT_CANVAS_SCOPES = [
    # Courses
    'url:GET|/api/v1/courses/:id',
    # Tabs
    'url:GET|/api/v1/courses/:course_id/tabs',
    'url:PUT|/api/v1/courses/:course_id/tabs/:tab_id',
    # External Tools
    'url:GET|/api/v1/courses/:course_id/external_tools',
    'url:GET|/api/v1/courses/:course_id/external_tools/sessionless_launch',
    'url:GET|/api/v1/courses/:course_id/external_tools/:external_tool_id',
]