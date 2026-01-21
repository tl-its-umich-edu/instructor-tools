import React, { useState } from 'react';
import { ContentCategoryForReview, CONTENT_CATEGORY_FOR_REVIEW } from '../constants';
import ArrowBack from '@mui/icons-material/ArrowBack';
import { Button, Grid, Box, Pagination, LinearProgress, styled, FormControl, InputLabel, Select, MenuItem, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import ContentImageCard from './ContentImageCard';
import { getContentImages } from '../api';
import { ContentItem, ContentImage, ContentImageEnriched, ActionType, ContentImageReviewState } from '../interfaces';
import ErrorsDisplay from './ErrorsDisplay';
import ReviewSummary from './ReviewSummary';

const Container = styled(Box)(({ theme }) => ({
  padding: theme.spacing(3),
  maxWidth: 1200,
  margin: '0 auto',
  backgroundColor: theme.palette.grey[50],
  minHeight: '100vh',
}));

const Header = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(2),
  marginBottom: theme.spacing(2),
  backgroundColor: 'white',
  padding: theme.spacing(2),
  borderRadius: theme.spacing(1),
}));

const ProgressBar = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  backgroundColor: 'white',
  padding: theme.spacing(2),
  borderRadius: theme.spacing(1),
}));

const ProgressBarFill = styled(Box)<{ progress: number }>(({ theme, progress }) => ({
  height: 8,
  backgroundColor: theme.palette.primary.main,
  borderRadius: 4,
  width: `${progress}%`,
  transition: 'width 0.3s ease',
}));

const TopControls = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  backgroundColor: 'white',
  padding: theme.spacing(2),
  borderRadius: theme.spacing(1),
}));

const BottomControls = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginTop: theme.spacing(3),
  gap: theme.spacing(2),
  backgroundColor: 'white',
  padding: theme.spacing(2),
  borderRadius: theme.spacing(1),
  [theme.breakpoints.down('sm')]: {
    flexDirection: 'column',
    alignItems: 'stretch',
  },
}));

interface AltTextReviewProps {
  categoryForReview: ContentCategoryForReview
  onEndReview: () => void
}

export default function AltTextReview( {categoryForReview, onEndReview} :AltTextReviewProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [reviewStates, setReviewStates] = useState<Record<string, ContentImageReviewState>>({});
  const [allImages, setAllImages] = useState<ContentImageEnriched[]>([]);
  const [showSummary, setShowSummary] = useState(false);
  const imagesPerPage = 6; // 2 images per row × 3 rows (6 total)

  const contentTypeFromCategory = (category: ContentCategoryForReview): 'assignment' | 'page' | 'quiz' => {
    if (category === CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS) return 'assignment';
    if (category === CONTENT_CATEGORY_FOR_REVIEW.PAGES) return 'page';
    return 'quiz';
  };

  const { data: contentItems, isFetching, error } = useQuery<ContentItem[], Error>({
    queryKey: ['contentImages', categoryForReview],
    queryFn: () => getContentImages(contentTypeFromCategory(categoryForReview)),
    enabled: !!categoryForReview,
    retry: false,
    retryOnMount: false, 
    onSuccess: (data) => {
      // Flatten and transform images
      const newImages = data.flatMap(ci =>
        ci.images.map((img: ContentImage) => ({ 
          ...img, 
          ...ci 
        }))
      );
      setAllImages(newImages);

      // Initialize reviewStates with all images
      const initialStates = newImages.reduce((acc, img) => {
        const key = String(img.image_id);
        acc[key] = {
          action: 'unreviewed',
          altText: img.image_alt_text ?? '',
          isDirty: false,
        };
        return acc;
      }, {} as Record<string, ContentImageReviewState>);
      setReviewStates(initialStates);
    },
  });

  const totalPages = Math.ceil(allImages.length / imagesPerPage);
  const startIdx = (currentPage - 1) * imagesPerPage;
  const paginatedImages = allImages.slice(startIdx, startIdx + imagesPerPage);
  const isLastPage = currentPage === totalPages;

  const imagesById: Record<string, ContentImageEnriched> = allImages.reduce((acc, img) => {
    acc[String(img.image_id)] = img;
    return acc;
  }, {} as Record<string, ContentImageEnriched>);

  const handleGoBack = () => {
    onEndReview();
  };
  
  const handleActionChange = (imageId: string, action: ActionType) => {
    setReviewStates(prev => ({
      ...prev,
      [imageId]: {
        ...prev[imageId],
        action,
      },
    }));
  };
  
  const handleAltTextChange = (imageId: string, newText: string) => {
    setReviewStates(prev => {
      const currentState = prev[imageId];
      const originalText = imagesById[imageId]?.image_alt_text ?? '';
      return {
        ...prev,
        [imageId]: {
          ...currentState,
          altText: newText,
          isDirty: newText !== originalText,
        },
      };
    });
  };
  const handleSetPageAs = (action: ActionType) => {
    setReviewStates(prev => {
      const newStates = { ...prev };
      paginatedImages.forEach(img => {
        const key = img.image_id;
        newStates[key] = {
          ...newStates[key],
          action,
        };
      });
      return newStates;
    });
  };

  const handlePageChange = (_: React.ChangeEvent<unknown>, page: number) => {
    setCurrentPage(page);
  };

  const getReviewedCount = () => {
    return Object.values(reviewStates).filter(state => state.action !== 'unreviewed').length;
  };

  const reviewedCount = getReviewedCount();
  const progressPercentage = allImages.length > 0 ? (reviewedCount / allImages.length) * 100 : 0;

  const errors = [error].filter(e => e !== null) as Error[];
  let feedbackBlock;
  if (isFetching || errors.length > 0) {
    feedbackBlock = (
      <Box sx={{ margin: 2 }}>
        {isFetching && <LinearProgress id='tool-card-container-loading' sx={{ marginBottom: 2 }} />}
        {errors.length > 0 && <Box sx={{ marginBottom: 1 }}><ErrorsDisplay errors={errors} /></Box>}
      </Box>
    );
  }

  return (
    <Container>
      {showSummary ? (
        <ReviewSummary 
          reviewStates={reviewStates}
          imagesById={imagesById}
          closeSummary={() => setShowSummary(false)}
          handleDone={() => handleGoBack()}
        />
      ) : (
        <>
          <Header>
            <Button startIcon={<ArrowBack />} onClick={handleGoBack} sx={{ mr: 'auto' }}>
          Go Back
            </Button>
          </Header>

          <Box sx={{ backgroundColor: 'white', padding: 3, borderRadius: 1, mb: 3 }}>
            <Typography variant="h5" gutterBottom fontWeight={600}>
          Review Alt Text
            </Typography>
            <Typography variant="body2" color="text.secondary">
          Review and approve AI-generated alt text for your courseware images
            </Typography>
          </Box>

          <ProgressBar>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2" fontWeight={500}>
            Progress: {reviewedCount} of {allImages.length} reviewed
              </Typography>
              <Typography variant="body2" color="text.secondary">
            Page {currentPage} of {totalPages}
              </Typography>
            </Box>
            <Box sx={{ backgroundColor: 'rgba(0,0,0,0.1)', borderRadius: 1, height: 8 }}>
              <ProgressBarFill progress={progressPercentage} />
            </Box>
          </ProgressBar>
          {feedbackBlock}
          {contentItems && (
            <>
              <TopControls>
                <FormControl fullWidth size="small">
                  <InputLabel>Set {paginatedImages.length} alt text label{paginatedImages.length !== 1 ? 's' : ''} as</InputLabel>
                  <Select
                    value=""
                    label={`Set ${paginatedImages.length} alt text label${paginatedImages.length !== 1 ? 's' : ''} as`}
                    onChange={(e) => handleSetPageAs(e.target.value as ActionType)}
                  >
                    <MenuItem value="approve">Approve</MenuItem>
                    <MenuItem value="skip">Skip for now</MenuItem>
                  </Select>
                </FormControl>
              </TopControls>
              <Grid container spacing={3}>
                {paginatedImages.map((imgData) => {
                  const key = String(imgData.image_id);
                  const state = reviewStates[key];

                  return (
                    <Grid item xs={12} sm={6} lg={6} key={`${imgData.content_name}-${key}`}>
                      <ContentImageCard
                        contentImage={imgData}
                        action={state.action}
                        altText={state.altText}
                        onActionChange={(action) => handleActionChange(key, action)}
                        onAltTextChange={(text) => handleAltTextChange(key, text)}
                      />
                    </Grid>
                  );
                })}
              </Grid>
              <BottomControls>
                {totalPages > 1 && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                    <Pagination 
                      count={totalPages} 
                      page={currentPage} 
                      onChange={handlePageChange}
                      siblingCount={0}
                    />
                  </Box>
                )}
                <Box sx={{ minWidth: 200, display: 'flex', justifyContent: 'flex-end' }}>
                  {isLastPage ? (
                    <Button
                      variant="contained"
                      onClick={() => setShowSummary(true)}
                      size="large"
                    >
                  Go to Summary
                    </Button>
                  ) : (
                    <Button
                      variant="outlined"
                      onClick={() => setCurrentPage(currentPage + 1)}
                    >
                  Next Page
                    </Button>
                  )}
                </Box>
              </BottomControls>
            </>
          )}
        </>)
      
      }
    </Container>
  );
}