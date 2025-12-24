DEFAUlT_CANVAS_SCOPES = [
    # Courses
    'url:GET|/api/v1/courses/:id',
    # Tabs
    'url:GET|/api/v1/courses/:course_id/tabs',
    'url:PUT|/api/v1/courses/:course_id/tabs/:tab_id',
    # Assignments
    'url:GET|/api/v1/courses/:course_id/assignments',
    # Pages
    'url:GET|/api/v1/courses/:course_id/pages',
    # Quizzes
    'url:GET|/api/v1/courses/:course_id/quizzes',
    'url:GET|/api/v1/courses/:course_id/quizzes/:quiz_id/questions',
]
