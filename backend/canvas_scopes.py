DEFAULT_CANVAS_SCOPES = [
    # Assignments
    'url:GET|/api/v1/courses/:course_id/assignments',
    'url:PUT|/api/v1/courses/:course_id/assignments/:id',
    # Courses
    'url:GET|/api/v1/courses/:id',
    # Pages
    'url:GET|/api/v1/courses/:course_id/pages',
    'url:PUT|/api/v1/courses/:course_id/pages/:url_or_id',
    # Tabs
    'url:GET|/api/v1/courses/:course_id/tabs',
    'url:PUT|/api/v1/courses/:course_id/tabs/:tab_id',
    # Quizzes
    'url:GET|/api/v1/courses/:course_id/quizzes',
    'url:PUT|/api/v1/courses/:course_id/quizzes/:id',
    # Quiz Questions
    'url:GET|/api/v1/courses/:course_id/quizzes/:quiz_id/questions',
    'url:PUT|/api/v1/courses/:course_id/quizzes/:quiz_id/questions/:id',
]
