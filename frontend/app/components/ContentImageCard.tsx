import React, { useState, useEffect } from 'react';
import { Card, CardMedia, CardContent, TextField, Box, Typography, styled, Button, Chip, Link } from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import type { ActionType, ContentImageEnriched } from '../interfaces';

const StyledCard = styled(Card)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  borderRadius: theme.spacing(1.5),
  border: '2px solid',
  borderColor: theme.palette.divider,
}));

const ActionButton = styled(Button)<{ selected?: boolean }>(({ theme, selected }) => ({
  flex: 1,
  minWidth: 0,
  padding: theme.spacing(1, 1.5),
  fontSize: '0.875rem',
  fontWeight: 500,
  textTransform: 'none',
  borderRadius: theme.spacing(0.75),
  border: '1px solid',
  borderColor: selected ? theme.palette.primary.main : theme.palette.divider,
  backgroundColor: selected ? theme.palette.primary.main : 'transparent',
  color: selected ? theme.palette.primary.contrastText : theme.palette.text.primary,
  '&:hover': {
    borderColor: theme.palette.primary.main,
    backgroundColor: selected ? theme.palette.primary.dark : theme.palette.action.hover,
  },
}));

const StatusChip = styled(Chip)(() => ({
  alignSelf: 'flex-start',
  fontWeight: 500,
  fontSize: '0.75rem',
}));

const CardHeader = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  paddingBottom: theme.spacing(1),
  borderBottom: `1px solid ${theme.palette.divider}`,
}));

interface ContentImageCardProps {
  contentImage: ContentImageEnriched;
  action: ActionType;
  altText: string;
  onActionChange: (action: ActionType) => void;
  onAltTextChange: (newText: string) => void;
}

export default function ContentImageCard({ 
  contentImage,
  action = 'unreviewed',
  altText,
  onActionChange,
  onAltTextChange 
}: ContentImageCardProps) {
  const [localAltText, setLocalAltText] = useState<string>(altText ?? '');

  // Sync local state with prop when it changes
  useEffect(() => {
    if (altText !== undefined && altText !== null) {
      setLocalAltText(altText);
    }
  }, [altText]);

  const handleActionChange = (newAction: ActionType) => {
    if (onActionChange) {
      onActionChange(newAction);
    }
  };

  const handleAltTextChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setLocalAltText(newValue);
    if (onAltTextChange) {
      onAltTextChange(newValue);
    }
  };

  const getStatusChip = () => {
    if (action === 'approve') {
      return <StatusChip icon={<CheckIcon />} label="Approved" color="primary" size="small" />;
    } else if (action === 'skip') {
      return <StatusChip icon={<AccessTimeIcon />} label="Skipped for now" size="small" />;
    }
    return <StatusChip label="Not yet reviewed" size="small" />;
  };

  return (
    <StyledCard>
      <CardHeader>
        {contentImage.canvas_link_url ? (
          <Link
            href={contentImage.canvas_link_url}
            target="_blank"
            rel="noopener noreferrer"
            fontWeight={600}
            noWrap
            sx={{
              display: 'block',
            }}
          >
            {contentImage.content_parent_name 
              ? `${contentImage.content_parent_name} : ${contentImage.content_name || 'Untitled'}` 
              : (contentImage.content_name || 'Untitled')}
          </Link>
        ) : (
          <Typography variant="subtitle1" fontWeight={600} noWrap>
            {contentImage.content_parent_name 
              ? `${contentImage.content_parent_name} : ${contentImage.content_name || 'Untitled'}` 
              : (contentImage.content_name || 'Untitled')}
          </Typography>
        )}
      </CardHeader>
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 1 }}>
        <CardMedia
          component="img"
          image={contentImage.image_url}
          alt={localAltText || String(contentImage.image_id)}
          sx={{ width: '100%', height: 240, objectFit: 'contain' }}
        />
      </Box>
      <CardContent sx={{ pt: 1, flexGrow: 1 }}>
        <Box>
          <Box sx={{display: 'flex', alignItems: 'center', gap: 0.5, marginBottom: 0.5}}>
            <Typography variant="body2">
              Alt Text Label:
            </Typography>
            {getStatusChip()}
          </Box>
          <TextField
            value={localAltText}
            onChange={handleAltTextChange}
            size="small"
            fullWidth
            multiline
            rows={2}
            inputProps={{ maxLength: 300 }}
            placeholder="Enter alt text description..."
          />
          <Typography variant="body2">
            {localAltText.length} / 300
          </Typography>
        </Box>
        <Box sx={{display: 'flex', gap: 1, width: '100%',}}>
          <ActionButton 
            selected={action === 'approve'}
            startIcon={<CheckIcon />}
            onClick={() => handleActionChange('approve')}
          >
            Approve
          </ActionButton>
          <ActionButton 
            selected={action === 'skip'}
            startIcon={<AccessTimeIcon />}
            onClick={() => handleActionChange('skip')}
          >
            Skip
          </ActionButton>
        </Box>
      </CardContent>
    </StyledCard>
  );
}
