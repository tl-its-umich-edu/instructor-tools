import { AltTextLastScanCourseContentItem, ActionType } from './interfaces';

export const imageSum = (contentItems: AltTextLastScanCourseContentItem[]): number => 
  contentItems.reduce((sum, item) => sum + item.image_count, 0);

/**
 * Maps internal ActionType values to user-facing labels for UI display and accessibility announcements.
 * This ensures consistency across all components and makes it easier to update labels when new actions are added.
 * @param action - The internal ActionType value
 * @returns User-facing label for the action
 */
export const getActionLabel = (action: ActionType): string => {
  switch (action) {
    case 'approve':
      return 'Approved';
    case 'skip':
      return 'Skipped for now';
    case 'decorative':
      return 'Decorative';
    case 'unreviewed':
    default:
      return 'Not yet reviewed';
  }
};