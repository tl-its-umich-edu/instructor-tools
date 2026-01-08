import React from 'react';
import { Card, CardMedia, CardContent, TextField, Box } from '@mui/material';
import type { ContentImage } from '../interfaces';

interface Props {
  image: ContentImage;
  width?: number | string; // e.g. 320 or '100%'
  altText?: string | null;
  onAltTextChange?: (newText: string) => void;
}

export default function ContentImageCard({ image, width = 320, altText, onAltTextChange }: Props) {
  const displayAlt = altText !== undefined ? altText ?? '' : image.image_alt_text ?? '';

  return (
    <Card sx={{ width, display: 'flex', flexDirection: 'column', alignItems: 'stretch' }}>
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', p: 1 }}>
        <CardMedia
          component="img"
          image={image.image_url}
          alt={displayAlt || String(image.image_id)}
          sx={{ width: '100%', height: 240, objectFit: 'contain' }}
        />
      </Box>
      <CardContent sx={{ pt: 1, flexGrow: 1 }}>
        <TextField
          label="Alt text"
          value={displayAlt}
          onChange={(e) => onAltTextChange && onAltTextChange(e.target.value)}
          size="small"
          fullWidth
          multiline
          rows={3}
          inputProps={{ maxLength: 150 }}
        />
      </CardContent>
    </Card>
  );
}
