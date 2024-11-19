import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Grid, LinearProgress, Snackbar, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';

import ErrorsDisplay from './ErrorsDisplay';
import HeaderAppBar from './HeaderAppBar';
import ToolCard from './ToolCard';
import { getTools } from '../api';
import constants from '../constants';
import '../css/Home.css';
import { Globals, Tool } from '../interfaces';

const MainContainer = styled('div')(({ theme }) => ({
  marginTop: theme.spacing(3),
  marginBottom: theme.spacing(3)
}));

const filterTools = (tools: Tool[], filter: string): Tool[] => {
  const filterLower = filter.toLowerCase();
  return tools.filter(
    (tool) => (
      tool.name.toLowerCase().includes(filterLower) ||
      tool.short_description.toLowerCase().includes(filterLower))
  );
};

interface HomeProps {
  globals: Globals
}

function Home (props: HomeProps) {
  const { globals } = props;

  const [tools, setTools] = useState<undefined | Tool[]>(undefined);
  const [searchFilter, setSearchFilter] = useState('');
  const [showRefreshAlert, setShowRefreshAlert] = useState<undefined | boolean>(undefined);

  const { isLoading: getToolsLoading, error: getToolsError } = useQuery(['getTools'], getTools, {
    onSuccess: (data) => setTools(data)
  });

  const onToolUpdate = (newTool: Tool) => {
    /*
    Creates new array with newTool replacing its previous version;
    Uses function inside setState hook to handle overlapping requests
    */
    setTools((oldTools) => {
      if (oldTools === undefined) throw Error('Expected tools variable to be defined!');
      const newTools = oldTools.map(t => t.canvas_id === newTool.canvas_id ? newTool : t);
      return newTools;
    });

    if (showRefreshAlert === undefined) setShowRefreshAlert(true);
  };

  const handleRefreshAlertClose = () => setShowRefreshAlert(false);

  const isLoading = getToolsLoading;
  const errors = [getToolsError].filter(e => e !== null) as Error[];

  let feedbackBlock;
  if (isLoading || errors.length > 0) {
    feedbackBlock = (
      <Box sx={{ margin: 2 }}>
        {isLoading && <LinearProgress id='tool-card-container-loading' sx={{ marginBottom: 2 }} />}
        {errors.length > 0 && <Box sx={{ marginBottom: 1 }}><ErrorsDisplay errors={errors} /></Box>}
      </Box>
    );
  }

  let toolCardContainer;
  let toolNumString = '0';
  if (tools !== undefined) {
    const filteredTools = searchFilter !== '' ? filterTools(tools, searchFilter) : tools;
    toolNumString = `${filteredTools.length} of ${tools.length}`;
    toolCardContainer = (
      <Grid container spacing={2} justifyContent='center'>
        {
          filteredTools.length > 0
            ? filteredTools.map(t => (
              <Grid item key={t.canvas_id}><ToolCard tool={t} onToolUpdate={onToolUpdate} /></Grid>
            ))
            : <Grid item><Alert severity='info'>No matching results</Alert></Grid>
        }
      </Grid>
    );
  }

  return (
    <div id='root'>
      <HeaderAppBar user={globals.user} helpURL={globals.help_url} onFilterChange={(v) => setSearchFilter(v)} />
      <MainContainer>
        <Typography variant='h6' component='h2' sx={{ textAlign: 'center', marginBottom: 3 }}>
          Instructor Tools is a collection of tools and resources to improve the online experience for you and your students.
        </Typography>
        {feedbackBlock}
        <Grid container justifyContent='center' sx={{ marginBottom: 2 }}>
          <Grid item>
            <Typography aria-live='polite' aria-atomic>{toolNumString} tools displayed</Typography>
          </Grid>
        </Grid>
        <div aria-describedby='tool-card-container-loading' aria-busy={getToolsLoading}>
          {toolCardContainer}
        </div>
      </MainContainer>
      <Typography component='footer' sx={{ textAlign: 'center' }}>
        Copyright © 2024 The Regents of the University of Michigan
      </Typography>
      <Snackbar open={showRefreshAlert} onClose={handleRefreshAlertClose} autoHideDuration={10000}>
        <Alert severity='info' elevation={2} onClose={handleRefreshAlertClose}>
          Refresh the page to update the tool&apos;s appearance in the {constants.toolMenuName}.
        </Alert>
      </Snackbar>
    </div>
  );
}

export default Home;
