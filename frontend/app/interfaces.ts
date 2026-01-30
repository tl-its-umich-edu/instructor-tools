interface User {
  username: string
  is_staff: boolean
}

interface Globals {
  user: User | null
  course_id: number
  course_name: string | null
  term_id: number | null
  term_name: string | null
  account_id: number | null
  account_name: string | null
  help_url: string
  ai_services_url: string
  google_analytics_id: string
  um_consent_manager_script_domain: string
}

interface CanvasPlacement {
  name: string
}

interface ToolCategory {
  id: number,
  category_name: string
}

interface Tool {
  id: number,
  name: string,
  canvas_id: number,
  logo_image: string | null,
  logo_image_alt_text: string | null,
  short_description: string,
  long_description: string,
  main_image: string | null,
  main_image_alt_text: string | null,
  privacy_agreement: string,
  canvas_placement_expanded: CanvasPlacement[],
  tool_categories_expanded: ToolCategory[]
  support_resources: string
  navigation_enabled: boolean
  launch_url: string
}

interface ToolFiltersState {
  search: string,
  categoryIds: number[]
}

interface AltTextScan {
  id: number
  course_id: number
  q_task_id: string
  status: string,
  created_at: string,
  updated_at: string
}

interface AltTextLastScanCourseContentItem {
  id: number, 
  canvas_id: number,
  canvas_name: string,
  image_count: number,
}
interface AltTextLastScanCourseContentByType {
  assignment_list: AltTextLastScanCourseContentItem[],
  page_list: AltTextLastScanCourseContentItem[],
  quiz_list: AltTextLastScanCourseContentItem[],
  quiz_question_list: AltTextLastScanCourseContentItem[]
}
interface AltTextLastScanDetail {
  id: number
  course_id: number,
  status: string,
  created_at: string,
  updated_at: string,
  course_content: AltTextLastScanCourseContentByType,
}

interface ContentImage {
  image_url: string
  image_id: number | string
  image_alt_text: string | null
  canvas_link_url: string | null
}

interface ContentItem {
  content_id: number
  content_name: string | null
  content_parent_id: number | null
  content_type: string
  images: ContentImage[]
}

interface ContentImageEnriched extends ContentImage {
  content_id: number
  content_name: string | null
  content_parent_id: number | null
  content_type: string
}


type ActionType = 'approve' | 'skip' | 'unreviewed';
interface ContentImageReviewState {
  action: ActionType;
  altText: string;
  isDirty: boolean;
}

interface ContentReviewRequestImageAction {
  image_url: string
  image_id: string
  action: 'approve' | 'skip'
  approved_alt_text: string
}
interface ContentReviewRequest {
  content_id: number
  content_name: string | null
  content_parent_id: number | null
  content_type: string
  images: ContentReviewRequestImageAction[]
}

export type { Globals, Tool, User, ToolCategory, ToolFiltersState, 
  AltTextScan, AltTextLastScanDetail, AltTextLastScanCourseContentItem, 
  ContentImage, ContentItem, ContentImageEnriched, ActionType, ContentImageReviewState,
  ContentReviewRequest };
