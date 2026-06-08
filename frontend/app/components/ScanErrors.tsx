import { Accordion, AccordionDetails, AccordionSummary, Alert, Box, Link, Stack, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import React, { useId, useState } from 'react';
import { CourseScanError } from '../interfaces';

interface ScanErrorsProps {
  scanErrors: CourseScanError[];
  totalImageCount: number;
}

export default function ScanErrors(props: ScanErrorsProps) {
  const { scanErrors, totalImageCount } = props;
  const [errorsExpanded, setErrorsExpanded] = useState(false);
  const accordionId = useId();
  const summaryId = `${accordionId}-summary`;
  const detailsId = `${accordionId}-details`;

  if (scanErrors.length === 0) {
    return null;
  }

  const isCompleteFail = totalImageCount === 0;
  const severity = isCompleteFail ? 'error' : 'warning';
  const borderColor = isCompleteFail ? 'error.main' : 'warning.dark';
  const severityLabel = isCompleteFail ? 'Error' : 'Warning';
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
      sx={{ marginBottom: 2, border: '2px solid', borderColor }}
    >
      <AccordionSummary id={summaryId} aria-controls={detailsId} expandIcon={<ExpandMoreIcon />}>
        <Alert severity={severity} sx={{ width: '100%', padding: 0, background: 'transparent' }} icon={false}>
          <Typography variant='body2'>
            <strong>{severityLabel}:</strong> <strong>{summaryText}</strong> - {actionText}
          </Typography>
        </Alert>
      </AccordionSummary>
      <AccordionDetails id={detailsId} aria-labelledby={summaryId}>
        <Stack component='ol' spacing={1} sx={{ margin: 0, paddingLeft: 3 }}>
          {scanErrors.map((error) => (
            <Box component='li' key={error.id}>
              <Typography variant='body2'>
                <strong>{error.error_type}</strong>
                {error.error_title && <> ({error.error_title})</>}
                : {error.error_message}
              </Typography>
              {error.canvas_url && (
                <Typography variant='body2'>
                  <Link
                    href={error.canvas_url}
                    target="_blank"
                    rel="noopener"
                    aria-label={`View "${error.error_title || 'Course'}" in Canvas - ${error.remediation_message} (opens in new tab)`}
                    sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
                  >
                    {`View "${error.error_title || 'Course'}" in Canvas - ${error.remediation_message}`}
                    <OpenInNewIcon fontSize="inherit" aria-hidden="true" />
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
