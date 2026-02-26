import React, { useEffect, useMemo, useState } from 'react';
import { AltTextLastScanCourseContentItem, AltTextLastScanDetail as ScanDetail } from '../interfaces';
import { Button, FormControl, InputLabel, MenuItem, Select, Stack, Typography } from '@mui/material';
import { CONTENT_CATEGORY_FOR_REVIEW, ContentCategoryForReview } from '../constants';
import { imageSum } from '../utils';


interface ReveiwSelectFormProps {
    scanPending: boolean;
    lastScan: ScanDetail;
    selectedCategory: ContentCategoryForReview;
    handleStartReview: (selectedCategory:ContentCategoryForReview) => void;
    handleChangeCategory: (selectedCategory:ContentCategoryForReview) => void;
}

export default function ReviewSelectForm({ scanPending, lastScan, selectedCategory, handleStartReview, handleChangeCategory }:ReveiwSelectFormProps) {
  // tuple associating Category value to respective label & sum of images to review
  const categoryToSumLabel: Record<ContentCategoryForReview, [string, number]> = useMemo(() => ({
    [CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS]: ['Assignments', imageSum(lastScan.course_content.assignment_list)],
    [CONTENT_CATEGORY_FOR_REVIEW.PAGES]: ['Pages', imageSum(lastScan.course_content.page_list)],
    [CONTENT_CATEGORY_FOR_REVIEW.CLASSIC_QUIZZES]: ['Classic Quizzes',
      imageSum(lastScan.course_content.quiz_list) + imageSum(lastScan.course_content.quiz_question_list)
    ],
  }), [lastScan.course_content]);

  const [numImagesSelected, setNumImagesSelected] = useState<number>(categoryToSumLabel[selectedCategory][1]);

  useEffect(() =>{
    setNumImagesSelected(categoryToSumLabel[selectedCategory][1]);
  }, [selectedCategory, categoryToSumLabel]);

  const handleSubmit = () => {
    if (selectedCategory) {
      handleStartReview(selectedCategory);
    }
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
            onChange={(e) => handleChangeCategory(e.target.value as ContentCategoryForReview)}
          >
            {Object.entries(categoryToSumLabel).map(([category, [label, sum]]) => {
              return (
                <MenuItem key={category} value={category}>
                  {label} - ({sum} images)
                </MenuItem>
              );
            })}
          </Select>
        </FormControl>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={(numImagesSelected === 0) || scanPending}
        >
            Begin Review
        </Button>
      </Stack>
    </>
  );
}