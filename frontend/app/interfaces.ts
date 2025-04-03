interface User {
  username: string
  is_staff: boolean
}

interface Globals {
  user: User | null
  help_url: string
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
  support_resources: string,
  navigation_enabled: boolean,
  sessionless_launch_url: string,
}

export type { Globals, Tool, User };
