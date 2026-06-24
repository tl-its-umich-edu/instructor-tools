import { AltTextLastScanCourseContentItem, ActionType } from './interfaces';

export const imageSum = (contentItems: AltTextLastScanCourseContentItem[]): number =>
  contentItems.reduce((sum, item) => sum + item.image_count, 0);

export const getActionLabels = (action: ActionType): { actionLabel: string; statusLabel: string } => {
  switch (action) {
  case 'approve':
    return { actionLabel: 'Approve', statusLabel: 'Approved' };
  case 'skip':
    return { actionLabel: 'Skip for now', statusLabel: 'Skipped for now' };
  case 'decorative':
    return { actionLabel: 'Mark as decorative', statusLabel: 'Marked decorative' };
  case 'unreviewed':
  default:
    return { actionLabel: 'Mark as unreviewed', statusLabel: 'Not yet reviewed' };
  }
};