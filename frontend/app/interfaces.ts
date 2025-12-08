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

interface SyncTask {
  id: number
  course_id: number
  q_task_id: string
  status: string,
}
export type { Globals, Tool, User, ToolCategory, ToolFiltersState, SyncTask};