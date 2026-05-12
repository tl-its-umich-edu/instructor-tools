import React, { useState, useEffect } from 'react';
import { Card, CardMedia, CardContent, TextField, Box, Typography, styled, Chip, Link, Tooltip, ToggleButton, ToggleButtonGroup } from '@mui/material';
import CheckIcon from '@mui/icons-material/Check';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import type { ActionType, ContentImageEnriched } from '../interfaces';

const StyledCard = styled(Card)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  height: '100%',
  borderRadius: theme.spacing(1.5),
  border: '2px solid',
  borderColor: theme.palette.divider,
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

const StyledToggleButtonGroup = styled(ToggleButtonGroup)(({ theme }) => ({
  width: '100%',
  '& .MuiToggleButtonGroup-grouped': {
    flex: 1,
    minWidth: 0,
    padding: theme.spacing(1, 1.5),
    fontSize: '0.875rem',
    fontWeight: 500,
    textTransform: 'none',
    color: theme.palette.text.primary,
    '&.Mui-selected': {
      color: theme.palette.primary.contrastText,
      backgroundColor: theme.palette.primary.main,
      '&:hover': {
        backgroundColor: theme.palette.primary.dark,
      },
    },
    '&:focus-visible': {
      boxShadow: `0 0 0 2px ${theme.palette.common.white}, 0 0 0 4px ${theme.palette.primary.main}`,
    },
  },
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

  const handleToggleChange = (_event: React.MouseEvent<HTMLElement>, newValue: ActionType | null) => {
    if (newValue !== null) {
      handleActionChange(newValue);
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
    } else if (action === 'decorative') {
      return <StatusChip icon={<VisibilityOffIcon />} label="Decorative" size="small" />;
    }
    return <StatusChip label="Not yet reviewed" size="small" />;
  };

  const getContentTitle = () => {
    return contentImage.content_parent_name 
      ? `${contentImage.content_parent_name} : ${contentImage.content_name}` 
      : contentImage.content_name;
  };

  const contentTitle = getContentTitle();

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
            {contentTitle}
          </Link>
        ) : (
          <Typography variant="subtitle1" fontWeight={600} noWrap>
            {contentTitle}
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
              Review Status:
            </Typography>
            {getStatusChip()}
          </Box>
          <TextField
            label="Alt Text"
            value={localAltText}
            onChange={handleAltTextChange}
            size="small"
            fullWidth
            multiline
            rows={2}
            inputProps={{ maxLength: 1000 }}
            placeholder="Enter alt text description..."
            disabled={action === 'decorative' || action === 'skip'}
          />
          <Typography variant="body2">
            {localAltText.length} characters
          </Typography>
        </Box>
        <StyledToggleButtonGroup
          value={action}
          exclusive
          onChange={handleToggleChange}
          fullWidth
          size="small"
          color="primary"
          aria-label="Image action"
        >
          <ToggleButton value="approve" aria-label="Approve">
            <CheckIcon sx={{ mr: 0.5, fontSize: '1.1rem' }} />
            Approve
          </ToggleButton>
          <Tooltip
            title="Skip for now — this image will be resurfaced on the next scan and is not updated."
            placement="top"
          >
            <ToggleButton value="skip" aria-label="Skip">
              <AccessTimeIcon sx={{ mr: 0.5, fontSize: '1.1rem' }} />
              Skip
            </ToggleButton>
          </Tooltip>
          <Tooltip
            title="Decorative images have no alt text and will be ignored by assistive technology."
            placement="top"
          >
            <ToggleButton value="decorative" aria-label="Decorative">
              <VisibilityOffIcon sx={{ mr: 0.5, fontSize: '1.1rem' }} />
              Decorative
            </ToggleButton>
          </Tooltip>
        </StyledToggleButtonGroup>
      </CardContent>
    </StyledCard>
  );
}
