import React, { useState } from 'react';
import { AltTextLastScanCourseContentItem, AltTextLastScanDetail as ScanDetail } from '../interfaces';
import { Button, FormControl, InputLabel, MenuItem, Select, Stack, Typography } from '@mui/material';
import { COURSE_CONTENT_CATEGORIES, CourseContentCategory } from '../constants';


interface ReveiwSelectFormProps {
    scanPending: boolean;
    lastScan: ScanDetail;
    handleStartReview: (categorySelected:CourseContentCategory) => void;
}

export default function ReviewSelectForm({ scanPending, lastScan, handleStartReview }:ReveiwSelectFormProps) {
  const [selectedCategory, setSelectedCategory] = useState<CourseContentCategory>(COURSE_CONTENT_CATEGORIES.ASSIGNMENT);
  
  const handleSubmit = () => {
    if (selectedCategory) {
      handleStartReview(selectedCategory);
    }
  };
  
  const imageSum = (contentItems : AltTextLastScanCourseContentItem[]) => {
    let result = 0;
    contentItems.forEach((item) => result += item.image_count);
    return result;
  };

  return (
    <>
      <Typography variant="h6" sx={{ mb: 1 }}>
        Start Review
      </Typography>
      <Typography variant="body2" sx={{ mb: 3 }}>
        Select which type of content to review first. You can review images by the available categories:
      </Typography>
      <Stack direction="row" spacing={2} alignItems='flex-end'>
        <FormControl sx={{ minWidth: 200 }} >
          <InputLabel>Content Category</InputLabel>
          <Select
            value={selectedCategory}
            label="Content Category"
            disabled={scanPending}
            onChange={(e) => setSelectedCategory(e.target.value as CourseContentCategory)}
          >
            <MenuItem value={COURSE_CONTENT_CATEGORIES.ASSIGNMENT}>
                  Assignments - ({imageSum(lastScan.course_content.assignment_list)} images)
            </MenuItem>
            <MenuItem value={COURSE_CONTENT_CATEGORIES.PAGE}>
                  Pages - ({imageSum(lastScan.course_content.page_list)} images)
            </MenuItem>
          </Select>
        </FormControl>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={scanPending}
        >
            Begin Review
        </Button>
      </Stack>
    </>
  );
}