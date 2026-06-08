import { Accordion, AccordionDetails, AccordionSummary, Box, Button, Divider, LinearProgress, Link, Typography, Alert, Stack } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { styled } from '@mui/material/styles';
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ErrorsDisplay from './ErrorsDisplay';
import { Globals, CourseScanError } from '../interfaces';
import LastScanInfo from './CourseScanComponent';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getAltTextLastScan, updateAltTextStartScan } from '../api';
import ReviewSelectForm from './ReviewSelectForm';
import { CONTENT_CATEGORY_FOR_REVIEW, ContentCategoryForReview, COURSE_SCAN_POLL_DURATION } from '../constants';

const TitleBlock = styled('div')(({ theme }) => ({
  marginTop: theme.spacing(3),
  marginBottom: theme.spacing(3)
}));

interface AltTextHomeProps {
  globals: Globals
}

function AltTextHome(props: AltTextHomeProps) {
  const { course_id, ai_services_url } = props.globals;
  const navigate = useNavigate();
  const [scanPending, setScanPending] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<ContentCategoryForReview>(CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS);
  const [scanErrors, setScanErrors] = useState<CourseScanError[]>([]);
  const [errorsExpanded, setErrorsExpanded] = useState(false);

  const { data: lastScan, 
    isLoading: lastScanIsLoading, 
    error: lastScanError, 
    isError: lastScanIsError
  } = useQuery({
    queryKey: ['scanStatus'],
    queryFn: async () => {
      return await getAltTextLastScan({ courseId: course_id }); 
    },
    refetchInterval: (data) => {
      if (data && typeof data === 'object' && 'scan_details' in data &&
        (data.scan_details.status == 'running' || data.scan_details.status == 'pending')
      ) {
        console.log('Last scan is in progress, waiting to refetch');
        return COURSE_SCAN_POLL_DURATION;
      } else {
        return false;
      }
    },
    onSuccess: (data) => {
      if (data && typeof data === 'object') {
        setScanPending(data.scan_details.status == 'running' || data.scan_details.status == 'pending');
        setScanErrors(data.scan_error_details || []);
      }
    }
  });

  const queryClient = useQueryClient();
  const { mutate } = useMutation({
    mutationFn: async () => {
      return await updateAltTextStartScan();
    },
    onSuccess: (data) => {
      if (data.status == 'running' || data.status=='pending') {
        setScanPending(true);
        queryClient.invalidateQueries({ queryKey: ['scanStatus'] });
      }
    },
  });

  const handleStartScan = async () => {
    setScanPending(true);
    await mutate();
  };

  const handleStartReview = (category: ContentCategoryForReview, scanId: number) => {
    navigate('/alt-text-helper/review', { state: { category, scanId } });
  };

  return (
    <>
      <TitleBlock>
        <Typography variant='h6' component='h2' sx={{ marginBottom: 1}}>
              Use AI suggestions to quickly apply alt-text labels to course images
        </Typography>
        <Typography variant='body2'>
              AI Disclaimer: This application uses UM-GPT toolkit to gather LLM-suggested alt text, powered by Azure OpenAI API.
        </Typography>
        <Typography variant='body2'>
          <Link href={ai_services_url} target="_blank" rel="noopener">
            Learn more about ITS AI Services
          </Link>
        </Typography>
      </TitleBlock>
      <Divider sx={{ marginBottom: 3}}/>
      {lastScanIsError && (
        <Box sx={{ marginBottom: 1 }}>
          <ErrorsDisplay errors={[lastScanError].filter(e => e !== null) as Error[]} />
        </Box>)}
      {lastScanIsLoading && (
        <Box sx={{ marginBottom: 1 }}>
          <LinearProgress id='last-scan-loading'/>
        </Box>
      )}
      {lastScan !== undefined && (
        <>
          {lastScan === false ? (
            <Box 
              display="flex"
              justifyContent="center"
              flexDirection="column"
              alignItems="center"
              sx={{ marginBottom: 3 }}
            >
              <Typography variant='body1' component='h2' sx={{ marginBottom: 3}}>
                To begin, start a scan of your course below:
              </Typography>
              <Button 
                variant='contained'
                onClick={handleStartScan}
                disabled={scanPending}
              >
                Start Scan
              </Button>
            </Box>
          ) : (
            <>
              {scanErrors.length > 0 && (() => {
                // A "complete failure" is when no images were fetched at all (total_image_count === 0).
                // In that case show error (red) severity; otherwise show warning (yellow) for partial failures.
                const isCompleteFail = lastScan.scan_details.total_image_count === 0;
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
              })()}
              <LastScanInfo
                scanPending={scanPending}
                lastScan={lastScan.scan_details}
                handleStartScan={handleStartScan}
              />
              {lastScan && (
                <ReviewSelectForm
                  scanPending={scanPending}
                  selectedCategory={selectedCategory}
                  lastScan={lastScan.scan_details}
                  handleStartReview={handleStartReview}
                  handleChangeCategory={(category) => setSelectedCategory(category)}
                />
              )}
            </>
          )}
        </>
      )}
    </>
    
  );
}

export default AltTextHome;