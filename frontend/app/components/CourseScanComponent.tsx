import { Accordion, AccordionActions, AccordionDetails, AccordionSummary, Box, Button, Grid, LinearProgress, Stack, Typography } from '@mui/material';
import React, { useMemo } from 'react';
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

interface LastScanInfoProps {
    scanPending: boolean;
    lastScan: ScanDetail;
    handleStartScan: () => void;
}

export default function LastScanInfo(props: LastScanInfoProps) {
  const { scanPending, lastScan, handleStartScan } = props;

  const scanUpdated = new Date(lastScan.updated_at);
  const scanCreated = new Date(lastScan.created_at);

  const scanContentSummaries = useMemo(() => ([
    {
      key: 'assignments',
      count: lastScan.course_content.assignment_list.length,
      labelSingular: 'Assignment',
      labelPlural: 'Assignments',
      imagesWithoutAlt: imageSum(lastScan.course_content.assignment_list),
    },
    {
      key: 'pages',
      count: lastScan.course_content.page_list.length,
      labelSingular: 'Page',
      labelPlural: 'Pages',
      imagesWithoutAlt: imageSum(lastScan.course_content.page_list),
    },
    {
      key: 'classic_quizzes',
      count: lastScan.course_content.quiz_list.length,
      labelSingular: 'Classic Quiz',
      labelPlural: 'Classic Quizzes',
      imagesWithoutAlt: imageSum(lastScan.course_content.quiz_list),
    },
    {
      key: 'classic_quiz_questions',
      count: lastScan.course_content.quiz_question_list.length,
      labelSingular: 'Classic Quiz Question',
      labelPlural: 'Classic Quiz Questions',
      imagesWithoutAlt: imageSum(lastScan.course_content.quiz_question_list),
    },
  ]), [lastScan.course_content]);

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
              :(lastScan && 
                <Box aria-describedby='scan-description-loading'>
                  {scanContentSummaries.map((item) => (
                    <Typography variant='body1' key={item.key}>
                      {item.count} {item.count === 1 ? item.labelSingular : item.labelPlural}
                      {item.imagesWithoutAlt > 0 && (
                        <> -- <b>{item.imagesWithoutAlt} {item.imagesWithoutAlt === 1 ? 'image' : 'images'}</b> without alt text</>
                      )}
                    </Typography>
                  ))}
                </Box>
              )}
          </AccordionDetails>
          <AccordionActions>
          </AccordionActions>
        </Accordion>
        
      </ScanInfoContainer>
      
    </>
  );
}