import React from 'react';
import { CourseContentCategory } from '../constants';
import { ArrowBack } from '@mui/icons-material';
import { Button } from '@mui/material';

interface AltTextReviewProps {
  category: CourseContentCategory
  onEndReview: () => void
}

export default function AltTextReview( {category, onEndReview} :AltTextReviewProps) {

  const handleGoBack = () => {
    onEndReview();
  };
  return <>
    <Button
      startIcon={<ArrowBack/>}
      onClick={handleGoBack}>
      Go Back
    </Button>
    <div>{'Category selected : ' + JSON.stringify(category)}</div>
  </>;
}