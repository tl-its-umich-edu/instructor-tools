const TOOL_MENU_NAME = 'Course Navigation Menu' as const;

const COURSE_CONTENT_CATEGORIES = {
  ASSIGNMENT: 'assignment',
  PAGE: 'page',
  QUIZ: 'quiz',
} as const;

type CourseContentCategory = typeof COURSE_CONTENT_CATEGORIES[keyof typeof COURSE_CONTENT_CATEGORIES]

export { TOOL_MENU_NAME, COURSE_CONTENT_CATEGORIES };
export type { CourseContentCategory };
