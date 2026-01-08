import React, { useState } from 'react';
import { ContentCategoryForReview, CONTENT_CATEGORY_FOR_REVIEW } from '../constants';
import ArrowBack from '@mui/icons-material/ArrowBack';
import { Button, Grid, Box, Pagination, LinearProgress } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import ContentImageCard from './ContentImageCard';
import { getContentImages } from '../api';
import { ContentItemResponse, ContentImage } from '../interfaces';
import ErrorsDisplay from './ErrorsDisplay';

interface AltTextReviewProps {
  categoryForReview: ContentCategoryForReview
  onEndReview: () => void
}

export default function AltTextReview( {categoryForReview, onEndReview} :AltTextReviewProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const imagesPerPage = 6; // 2 images per row × 3 rows (6 total)

  const contentTypeFromCategory = (category: ContentCategoryForReview): 'assignment' | 'page' | 'quiz' => {
    if (category === CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS) return 'assignment';
    if (category === CONTENT_CATEGORY_FOR_REVIEW.PAGES) return 'page';
    return 'quiz';
  };

  const { data: contentItems, isLoading, error } = useQuery<ContentItemResponse[], Error>({
    queryKey: ['contentImages', categoryForReview],
    queryFn: () => getContentImages(contentTypeFromCategory(categoryForReview)),
    enabled: !!categoryForReview,
    retry: false,
    retryOnMount: false, 
    staleTime: Infinity,
  });

  const [edits, setEdits] = React.useState<Record<string, string>>({});

  const allImages = contentItems?.flatMap(ci =>
    ci.images.map((img: ContentImage) => ({ ...img, contentName: ci.content_name }))
  ) ?? [];

  const totalPages = Math.ceil(allImages.length / imagesPerPage);
  const startIdx = (currentPage - 1) * imagesPerPage;
  const paginatedImages = allImages.slice(startIdx, startIdx + imagesPerPage);

  const handleAltTextChange = (imageId: string, newText: string) => {
    setEdits(prev => ({ ...prev, [imageId]: newText }));
  };

  const handleGoBack = () => {
    onEndReview();
  };

  const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
  };
  const errors = [error].filter(e => e !== null) as Error[];
  let feedbackBlock;
  if (isLoading || errors.length > 0) {
    feedbackBlock = (
      <Box sx={{ margin: 2 }}>
        {isLoading && <LinearProgress id='tool-card-container-loading' sx={{ marginBottom: 2 }} />}
        {errors.length > 0 && <Box sx={{ marginBottom: 1 }}><ErrorsDisplay errors={errors} /></Box>}
      </Box>
    );
  }

  return <>
    <Button startIcon={<ArrowBack/>} onClick={handleGoBack}>Go Back</Button>
    <div>{'Category selected : ' + JSON.stringify(categoryForReview)}</div>
    {feedbackBlock}
    {contentItems && (
      <div>
        <div>{`Found ${allImages.length} images`}</div>
        <Grid container spacing={1} sx={{ mt: 1, mb: 3 }}>
          {paginatedImages.map((imgData) => {
            const key = String(imgData.image_id);
            return (
              <Grid item xs={6} key={`${imgData.contentName}-${key}`}>
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <Box sx={{ mb: 1, textAlign: 'left', width: '100%' }}>
                    <strong>{imgData.contentName}</strong>
                  </Box>
                  <ContentImageCard
                    image={imgData}
                    altText={edits[key] ?? imgData.image_alt_text}
                    onAltTextChange={(val) => handleAltTextChange(key, val)}
                  />
                </Box>
              </Grid>
            );
          })}
        </Grid>
        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
            <Pagination count={totalPages} page={currentPage} onChange={handlePageChange} />
          </Box>
        )}
      </div>
    )}
  </>;
}