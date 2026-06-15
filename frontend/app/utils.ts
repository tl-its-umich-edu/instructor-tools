import { AltTextLastScanCourseContentItem, ActionType } from './interfaces';

export const imageSum = (contentItems: AltTextLastScanCourseContentItem[]): number =>
  contentItems.reduce((sum, item) => sum + item.image_count, 0);

/**
 * Maps internal ActionType values to both action and status labels.
 * Action labels are for controls and announcements.
 * Status labels are for chips and read-only state summaries.
 * @param action - The internal ActionType value
 * @returns User-facing action and status labels
 */
export const getActionLabels = (action: ActionType): { actionLabel: string; statusLabel: string } => {
  switch (action) {
    case 'approve':
      return { actionLabel: 'Approve', statusLabel: 'Approved' };
    case 'skip':
      return { actionLabel: 'Skip for now', statusLabel: 'Skipped for now' };
    case 'decorative':
      return { actionLabel: 'Decorative', statusLabel: 'Decorative' };
    case 'unreviewed':
    default:
      return { actionLabel: 'Mark as unreviewed', statusLabel: 'Not yet reviewed' };
  }
};