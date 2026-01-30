import { Accordion, AccordionActions, AccordionDetails, AccordionSummary, Box, Button, Grid, LinearProgress, Stack, Typography } from '@mui/material';
import React from 'react';
import { styled } from '@mui/material/styles';
import { AltTextLastScanDetail as ScanDetail } from '../interfaces';
import Refresh from '@mui/icons-material/Refresh';
import theme from '../theme';
import { imageSum } from '../utils';

const ScanInfoContainer = styled(Box)(() => ({
  marginTop: theme.spacing(3),
  display: 'flex',
  flexDirection:'column',
  justifyContent: 'center',
  marginBottom: theme.spacing(3),
}));

interface CourseScanComponentProps {
    scanPending: boolean;
    lastScan: ScanDetail | false;
    handleStartScan: () => void;
}

export default function CourseScanComponent(props: CourseScanComponentProps) {
  const { scanPending, lastScan, handleStartScan } = props;

  // Initial visit - no scan found
  if (!lastScan) {
    return (
      <Box 
        display="flex"
        justifyContent="center"
        flexDirection="column"
        alignItems="center">
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
    );
  }

  const scanUpdated = new Date(lastScan.updated_at);
  const scanCreated = new Date(lastScan.created_at);

  const descriptionBlock = (
    <Box aria-describedby='scan-description-loading'>
      <Typography variant='body1'>
        {lastScan.course_content.assignment_list.length} Assignments found -- <b>{imageSum(lastScan.course_content.assignment_list)} images</b> without alt text
      </Typography>
      <Typography variant='body1'>
        {lastScan.course_content.page_list.length} Pages found -- <b>{imageSum(lastScan.course_content.page_list)} images</b> without alt text
      </Typography>
      <Typography variant='body1'>
        {lastScan.course_content.quiz_list.length} Classic Quizzes found -- <b>{imageSum(lastScan.course_content.quiz_list)} images</b> without alt text
      </Typography>
      <Typography variant='body1'>
        {lastScan.course_content.quiz_question_list.length} Classic Quiz Questions found -- <b>{imageSum(lastScan.course_content.quiz_question_list)} images</b> without alt text
      </Typography>
    </Box>
  );

  const status = scanPending ? 'IN PROGRESS' :
    lastScan.status.toUpperCase();
  
  return (
    <>
      <ScanInfoContainer>
        <Stack direction="row" spacing={2}>
          <Typography variant='body1'>
            Below is your most recent scan for images in the course. To retrieve changes made since the last run, <b>start a new scan</b> :
          </Typography>
          <Button 
            startIcon={<Refresh />}
            variant='contained'
            onClick={handleStartScan}
            disabled={scanPending}
          >
            Rescan Course
          </Button>
        </Stack>
        <Accordion defaultExpanded>
          <AccordionSummary>
            <Grid container spacing={2} justifyContent='space-between' align-items='end'>
              <Grid item>
                <Typography variant='h5'>Course Scan ID: {lastScan.id} </Typography>
                <Typography variant='body1'>Last Updated: {scanUpdated.toLocaleString()} (first created {scanCreated.toLocaleDateString()})</Typography>
              </Grid>
              <Grid item>
                <Typography>Status: {status}</Typography>
              </Grid>
            </Grid>
            
          </AccordionSummary>
          <AccordionDetails>
            { scanPending ? 
              <LinearProgress id='scan-description-loading' />
              :(lastScan && descriptionBlock)}
          </AccordionDetails>
          <AccordionActions>
          </AccordionActions>
        </Accordion>
        
      </ScanInfoContainer>
      
    </>
  );
}