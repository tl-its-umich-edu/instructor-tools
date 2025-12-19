import { Accordion, AccordionActions, AccordionDetails, AccordionSummary, Box, Button, Grid, LinearProgress, Stack, Typography } from '@mui/material';
import React from 'react';
import { styled } from '@mui/material/styles';
import { AltTextLastScanDetail as ScanDetail } from '../interfaces';
import { Refresh } from '@mui/icons-material';
import theme from '../theme';

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
            Start Sync
        </Button>
      </Box>
    );
  }

  const descriptionBlock = (
    <Box aria-describedby='scan-description-loading'>
      <Typography>Task: {lastScan.id}</Typography>
      <Typography>Assignment Count: {lastScan.course_content.assignment_list.length}</Typography>
      <Typography>Pages Count: {lastScan.course_content.page_list.length}</Typography>
    </Box>
  );

  const status = scanPending ? 'IN PROGRESS' :
    lastScan.status;
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
                <Typography variant='h5'>Course Scan </Typography>
                <Typography variant='body1'>Updated: {lastScan.updated_at}</Typography>
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