import { AltTextLastScanCourseContentItem } from './interfaces';

export const imageSum = (contentItems: AltTextLastScanCourseContentItem[]): number => 
  contentItems.reduce((sum, item) => sum + item.image_count, 0);