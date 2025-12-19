import { Box, Button, Divider, LinearProgress, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';
import React, { useState } from 'react';
import ErrorsDisplay from './ErrorsDisplay';
import ArrowBack from '@mui/icons-material/ArrowBack';
import { Link } from 'react-router-dom';
import { AltTextLastScanDetail, AltTextScan, Globals } from '../interfaces';
import HeaderAppBar from './HeaderAppBar';
import CourseScanComponent from './CourseScanComponent';
// import { useQueryLastScan, useStartScan } from '../hooks/useAltTextQueryOptions';
import { isError, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getAltTextLastScan, updateAltTextStartScan } from '../api';
import { Refresh } from '@mui/icons-material';
import ReviewSelectForm from './ReviewSelectForm';
import AltTextReview from './AltTextReview';
import { CourseContentCategory } from '../constants';

const TitleBlock = styled('div')(({ theme }) => ({
  marginTop: theme.spacing(3),
  marginBottom: theme.spacing(3)
}));

interface AltTextHomeProps {
  globals: Globals
}

function AltTextHome (props: AltTextHomeProps) {
  const {course_id, user, help_url} = props.globals;
  const [scanPending, setScanPending] = useState(false);
  const [reviewCategoryStarted, setReviewCategoryStarted] = useState<CourseContentCategory>();

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
        return 2000;
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
    mutationFn: async (courseId : number) => {
      return await updateAltTextStartScan({ courseId });
    },
    onSuccess: (data) => {
      if (data.status == 'running' || data.status=='pending') {
        setScanPending(true);
        queryClient.invalidateQueries({ queryKey: ['scanStatus'] });
      }
    },
  });

  const handleStartScan = async () => {
    await mutate(course_id);
  };

  const handleStartReview = (category: CourseContentCategory ) => {
    setReviewCategoryStarted(category);
  };

  const handleEndReview = () => {
    setReviewCategoryStarted(undefined);
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
              category={reviewCategoryStarted}
              onEndReview={handleEndReview}
            />
          </>
        ) : (
          <>
            <TitleBlock>
              <Typography variant='h6' component='h2' sx={{ marginBottom: 1}}>
              Use AI suggestions to quickly apply alt-text labels to course images
              </Typography>
              <Typography variant='body1' component='h2'>
              AI Disclaimer: Learn more generative AI powered by UMGPT toolkit
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
                    lastScan={lastScan} 
                    handleStartReview={handleStartReview}/>
                )}
              </>
            )}
          </>
        )}
    </>
    
  );
}

export default AltTextHome;