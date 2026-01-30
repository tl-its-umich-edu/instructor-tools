import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ContentImageReviewState, ContentImageEnriched, ContentReviewRequest } from '../interfaces';
import { updateAltTextSubmitReview } from '../api';
import { Box, styled, Paper, Typography, Alert, Button, CircularProgress } from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import EditIcon from '@mui/icons-material/Edit';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

const SummaryContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(4),
  maxWidth: 1000,
  margin: '0 auto',
}));

const SummaryGrid = styled(Box)(({ theme }) => ({
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
  gap: theme.spacing(2),
  marginBottom: theme.spacing(4),
}));

const SummaryCard = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  textAlign: 'center',
  borderRadius: theme.spacing(1.5),
  border: `1px solid ${theme.palette.divider}`,
}));

const SummaryNumber = styled(Typography)(({ theme }) => ({
  fontSize: '2.5rem',
  fontWeight: 600,
  marginTop: theme.spacing(1),
  marginBottom: theme.spacing(0.5),
}));

const SummaryLabel = styled(Typography)(({ theme }) => ({
  fontSize: '0.875rem',
  color: theme.palette.text.secondary,
  fontWeight: 500,
}));

const IconWrapper = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  marginBottom: theme.spacing(1),
  '& svg': {
    fontSize: 32,
  },
}));

interface ReviewSummaryProps {
    reviewStates: Record<string, ContentImageReviewState>
    imagesById: Record<string, ContentImageEnriched>
    closeSummary: () => void;
    handleDone: () => void;
}

export default function ReviewSummary({
  reviewStates,
  imagesById,
  closeSummary,
  handleDone
}: ReviewSummaryProps) {
  const [submitResult, setSubmitResult] = useState<{ success: boolean; message: string } | null>(null);

  const mutation = useMutation({
    mutationFn: updateAltTextSubmitReview,
    onSuccess: () => {
      setSubmitResult({ success: true, message: 'Review submitted successfully!' });
    },
    onError: (error: Error) => {
      setSubmitResult({ success: false, message: error.message });
    }
  });

  const handleSubmit = () => {
    // Un-flatten review states into payload grouped by content_id, excluding unreviewed images
    const groupedByContent: Record<number, ContentReviewRequest> = {};

    Object.entries(reviewStates).forEach(([key, state]) => {
      // Skip unreviewed images
      if (state.action === 'unreviewed') return;

      const contentImage = imagesById[key];
      if (!contentImage) return;

      const { content_id, content_name, content_parent_id, content_type } = contentImage;

      if (!groupedByContent[content_id]) {
        groupedByContent[content_id] = {
          content_id,
          content_name,
          content_parent_id,
          content_type,
          images: []
        };
      }

      groupedByContent[content_id].images.push({
        image_url: contentImage.image_url,
        image_id: String(contentImage.image_id),
        action: state.action,
        approved_alt_text: state.altText
      });
    });

    const payload = Object.values(groupedByContent);
    mutation.mutate(payload);
  };

  const summary = {
    approved: 0,
    skipped: 0,
    modified: 0,
    unreviewed: 0
  };

  Object.keys(reviewStates).forEach(key => {
    const state = reviewStates[key];
    if (state.action === 'approve') summary.approved++;
    else if (state.action === 'skip') summary.skipped++;
    else if (state.action === 'unreviewed') summary.unreviewed++;

    if (state.isDirty) summary.modified++;
  });

  const noChangesToSubmit = summary.approved === 0 && summary.skipped === 0;

  return (
    <SummaryContainer>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h4" gutterBottom fontWeight={600}>
              Review Summary
        </Typography>
        <Typography variant="body1" color="text.secondary">
              Review your changes before final submission. <b>You cannot edit alt text in this app after saving approved changes.</b> To update alt text labels after saving, edit content in the course directly. 
        </Typography>
      </Box>

      {submitResult ? (
        <Box>
          <Alert severity={submitResult.success ? 'success' : 'error'} sx={{ mb: 3 }}>
            {submitResult.message}
          </Alert>
          <Button variant="contained" onClick={handleDone} fullWidth size="large">
                Done
          </Button>
        </Box>
      ) : (
        <>
          <SummaryGrid>
            <SummaryCard elevation={0}>
              <IconWrapper>
                <CheckIcon color="primary" />
              </IconWrapper>
              <SummaryLabel>Approved</SummaryLabel>
              <SummaryNumber>{summary.approved}</SummaryNumber>
            </SummaryCard>

            <SummaryCard elevation={0}>
              <IconWrapper>
                <EditIcon color="primary" />
              </IconWrapper>
              <SummaryLabel>Edited</SummaryLabel>
              <SummaryNumber>{summary.modified}</SummaryNumber>
            </SummaryCard>

            <SummaryCard elevation={0}>
              <IconWrapper>
                <AccessTimeIcon color="action" />
              </IconWrapper>
              <SummaryLabel>Skipped</SummaryLabel>
              <SummaryNumber>{summary.skipped}</SummaryNumber>
            </SummaryCard>
          </SummaryGrid>

          {summary.unreviewed > 0 && (
            <Alert severity="info" sx={{ mb: 3 }}>
              {summary.unreviewed} image{summary.unreviewed > 1 ? 's' : ''} remain unreviewed and will not be included in this submission.
            </Alert>
          )}
          {noChangesToSubmit && (
            <Alert severity="warning" sx={{ mb: 3 }}>
                There are no changes in this review to submit. Go back to review alt text labels.
            </Alert>
          )}

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button 
              onClick={() => closeSummary()} 
              variant="outlined"
              size="large"
              fullWidth
              disabled={mutation.isPending}
            >
                  Go Back
            </Button>
            <Button
              onClick={handleSubmit}
              variant="contained"
              disabled={mutation.isPending || noChangesToSubmit}
              size="large"
              fullWidth
              startIcon={mutation.isPending && <CircularProgress size={20} />}
            >
              {mutation.isPending ? 'Saving...' : 'Save All Changes'}
            </Button>
          </Box>
        </>
      )}
    </SummaryContainer>
  );
}