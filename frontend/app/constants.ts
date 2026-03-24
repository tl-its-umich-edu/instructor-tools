const TOOL_MENU_NAME = 'Course Navigation Menu' as const;

const COURSE_CONTENT_CATEGORIES = {
  ASSIGNMENT: 'assignment',
  PAGE: 'page',
  QUIZ: 'quiz',
  QUIZ_QUESTION: 'quiz_question',
} as const;

const CONTENT_CATEGORY_FOR_REVIEW = {
  ASSIGNMENTS: `${COURSE_CONTENT_CATEGORIES.ASSIGNMENT}s`,
  PAGES: `${COURSE_CONTENT_CATEGORIES.PAGE}s`,
  CLASSIC_QUIZZES: 'classic_quizzes',
} as const;

type CourseContentCategory = typeof COURSE_CONTENT_CATEGORIES[keyof typeof COURSE_CONTENT_CATEGORIES]
type ContentCategoryForReview = typeof CONTENT_CATEGORY_FOR_REVIEW[keyof typeof CONTENT_CATEGORY_FOR_REVIEW]

const CATEGORY_TO_CONTENT_TYPE: Record<ContentCategoryForReview, 'assignment' | 'page' | 'quiz'> = {
  [CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS]: 'assignment',
  [CONTENT_CATEGORY_FOR_REVIEW.PAGES]: 'page',
  [CONTENT_CATEGORY_FOR_REVIEW.CLASSIC_QUIZZES]: 'quiz',
};

const COURSE_SCAN_POLL_DURATION = 2000;

export { TOOL_MENU_NAME, COURSE_CONTENT_CATEGORIES, CONTENT_CATEGORY_FOR_REVIEW, CATEGORY_TO_CONTENT_TYPE, COURSE_SCAN_POLL_DURATION };
export type { CourseContentCategory, ContentCategoryForReview};
