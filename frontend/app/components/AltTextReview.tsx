import React from 'react';
import { ContentCategoryForReview, CONTENT_CATEGORY_FOR_REVIEW } from '../constants';
import ArrowBack from '@mui/icons-material/ArrowBack';
import { Button } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { getContentImages } from '../api';
import { ContentItemResponse, ContentImage } from '../interfaces';

interface AltTextReviewProps {
  categoryForReview: ContentCategoryForReview
  onEndReview: () => void
}

export default function AltTextReview( {categoryForReview, onEndReview} :AltTextReviewProps) {
  const contentTypeFromCategory = (category: ContentCategoryForReview): 'assignment' | 'page' | 'quiz' => {
    if (category === CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS) return 'assignment';
    if (category === CONTENT_CATEGORY_FOR_REVIEW.PAGES) return 'page';
    return 'quiz';
  };

  const { data: contentItems, isLoading, isError, error } = useQuery<ContentItemResponse[], Error>({
    queryKey: ['contentImages', categoryForReview],
    queryFn: () => getContentImages(contentTypeFromCategory(categoryForReview)),
    enabled: !!categoryForReview,
  });

  const handleGoBack = () => {
    onEndReview();
  };

  return <>
    <Button startIcon={<ArrowBack/>} onClick={handleGoBack}>Go Back</Button>
    <div>{'Category selected : ' + JSON.stringify(categoryForReview)}</div>
    {isLoading && <div>Loading content images…</div>}
    {isError && <div style={{color: 'red'}}>Error: {(error && error.message) || String(error)}</div>}
    {contentItems && (
      <div>
        <div>{`Found ${contentItems.length} content items`}</div>
        <ul>
          {contentItems.map(ci => (
            <li key={ci.content_id}>
              <strong>{ci.content_type} {ci.content_id}</strong> — {ci.images.length} images
              <ul>
                {ci.images.map((img: ContentImage) => (
                  <li key={String(img.image_id)}>{img.image_url}{img.image_alt_text ? ` — ${img.image_alt_text}` : ''}</li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </div>
    )}
  </>;
}