import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Link, Stack, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import React, { useState } from 'react';
import { CourseScanError } from '../interfaces';

interface ScanErrorsProps {
  scanErrors: CourseScanError[];
  totalImageCount: number;
}

export default function ScanErrors(props: ScanErrorsProps) {
  const { scanErrors, totalImageCount } = props;
  const [errorsExpanded, setErrorsExpanded] = useState(false);

  if (scanErrors.length === 0) {
    return null;
  }

  const isCompleteFail = totalImageCount === 0;
  const severity = isCompleteFail ? 'error' : 'warning';
  const borderColor = isCompleteFail ? 'error.main' : 'warning.main';
  const summaryText = isCompleteFail
    ? 'Scan completely failed'
    : `Scan encountered ${scanErrors.length} error(s) during processing`;
  const actionText = errorsExpanded
    ? 'collapse to hide details'
    : 'expand to view details';

  return (
    <Accordion
      expanded={errorsExpanded}
      onChange={(_, expanded) => setErrorsExpanded(expanded)}
      sx={{ marginBottom: 2, border: '1px solid', borderColor }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Alert severity={severity} sx={{ width: '100%', padding: 0, background: 'transparent' }} icon={false}>
          <Typography variant='body2'>
            <strong>{summaryText}</strong> - {actionText}
          </Typography>
        </Alert>
      </AccordionSummary>
      <AccordionDetails>
        <Stack spacing={1}>
          {scanErrors.map((error, index) => (
            <Box key={error.id} sx={{ paddingLeft: 2 }}>
              <Typography variant='body2'>
                <strong>{index + 1}. {error.error_type}</strong>
                {error.error_title && <> ({error.error_title})</>}
                : {error.error_message}
              </Typography>
              {error.canvas_url && (
                <Typography variant='body2'>
                  <Link href={error.canvas_url} target="_blank" rel="noopener">
                    {`View "${error.error_title || 'Course'}" in Canvas - ${error.remediation_message}`}
                  </Link>
                </Typography>
              )}
            </Box>
          ))}
        </Stack>
      </AccordionDetails>
    </Accordion>
  );
}
