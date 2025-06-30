interface User {
  username: string
  is_staff: boolean
}

interface Globals {
  user: User | null
  course_id: number
  help_url: string
  google_analytics_id: string
  um_consent_manager_script_domain: string
}

interface CanvasPlacement {
  name: string
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
  support_resources: string
  navigation_enabled: boolean
  launch_url: string
}

export type { Globals, Tool, User };
