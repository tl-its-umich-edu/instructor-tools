import React from 'react';
import { ContentCategoryForReview } from '../constants';
import ArrowBack from '@mui/icons-material/ArrowBack';
import { Button } from '@mui/material';

interface AltTextReviewProps {
  categoryForReview: ContentCategoryForReview
  onEndReview: () => void
}

export default function AltTextReview( {categoryForReview, onEndReview} :AltTextReviewProps) {

  const handleGoBack = () => {
    onEndReview();
  };
  return <>
    <Button
      startIcon={<ArrowBack/>}
      onClick={handleGoBack}>
      Go Back
    </Button>
    <div>{'Category selected : ' + JSON.stringify(categoryForReview)}</div>
  </>;
}