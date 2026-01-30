import { Box, Divider, LinearProgress, Link, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';
import React, { useState } from 'react';
import ErrorsDisplay from './ErrorsDisplay';
import { Globals } from '../interfaces';
import HeaderAppBar from './HeaderAppBar';
import CourseScanComponent from './CourseScanComponent';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getAltTextLastScan, updateAltTextStartScan } from '../api';
import ReviewSelectForm from './ReviewSelectForm';
import AltTextReview from './AltTextReview';
import { CONTENT_CATEGORY_FOR_REVIEW, ContentCategoryForReview, COURSE_SCAN_POLL_DURATION } from '../constants';

const TitleBlock = styled('div')(({ theme }) => ({
  marginTop: theme.spacing(3),
  marginBottom: theme.spacing(3)
}));

interface AltTextHomeProps {
  globals: Globals
}

function AltTextHome(props: AltTextHomeProps) {
  const { course_id, user, help_url, ai_services_url } = props.globals;
  const [scanPending, setScanPending] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<ContentCategoryForReview>(CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS);
  const [reviewCategoryStarted, setReviewCategoryStarted] = useState(false);

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
      if (!!data && 
        (data.status == 'running' || data.status == 'pending')
      ) {
        console.log('Last scan is in progress, waiting to refetch');
        return COURSE_SCAN_POLL_DURATION;
      } else {
        return false;
      }
    },
    onSuccess: (data) => {
      if (data) {
        setScanPending(data.status == 'running' || data.status == 'pending');
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

  const handleStartReview = () => {
    setReviewCategoryStarted(true);
  };

  const handleEndReview = () => {
    setSelectedCategory(CONTENT_CATEGORY_FOR_REVIEW.ASSIGNMENTS);
    setReviewCategoryStarted(false);
  };

  return (
    <>
      <HeaderAppBar 
        breadcrumbTitle='Alt Text Helper'
        user={user}
        helpURL={help_url}
      />
      {reviewCategoryStarted ? // Review view 
        (
          <>
            <AltTextReview 
              categoryForReview={selectedCategory}
              onEndReview={handleEndReview}
            />
          </>
        ) : (
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
                  Click here to learn more
                </Link> about ITS Generative AI services. 
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
                <CourseScanComponent
                  scanPending={scanPending}
                  lastScan={lastScan} 
                  handleStartScan={handleStartScan}
                />
                {lastScan && (
                  <ReviewSelectForm
                    scanPending={scanPending}
                    selectedCategory={selectedCategory}
                    lastScan={lastScan} 
                    handleStartReview={handleStartReview}
                    handleChangeCategory={(category) => setSelectedCategory(category)}/>
                )}
              </>
            )}
          </>
        )}
    </>
    
  );
}

export default AltTextHome;