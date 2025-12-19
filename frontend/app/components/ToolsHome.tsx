import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Alert, Box, Button, Grid, LinearProgress, Snackbar, Typography } from '@mui/material';
import { styled } from '@mui/material/styles';
import SearchIcon from '@mui/icons-material/Search';
import InputBase from '@mui/material/InputBase';

import ErrorsDisplay from './ErrorsDisplay';
import HeaderAppBar from './HeaderAppBar';
import ToolCard from './ToolCard';
import { getTools } from '../api';
import  { TOOL_MENU_NAME } from '../constants';
import '../css/ToolsHome.css';
import { Globals, Tool, ToolFiltersState } from '../interfaces';
import ToolFilters from './ToolFilters';

const MainContainer = styled('div')(({ theme }) => ({
  marginTop: theme.spacing(3),
  marginBottom: theme.spacing(3)
}));

const filterTools = (tools: Tool[], toolFiltersState: ToolFiltersState): Tool[] => {
  const searchLower = toolFiltersState.search.toLowerCase();
  return tools.filter(
    (tool) => {
      const matchesSearch = 
        toolFiltersState.search === '' ||
        tool.name.toLowerCase().includes(searchLower) ||
        tool.short_description.toLowerCase().includes(searchLower);

      const matchesCategory =
        toolFiltersState.categoryIds.length === 0 ||
        tool.tool_categories_expanded.some((tc) =>
          toolFiltersState.categoryIds.some((catId) => catId === tc.id)
        );

      return matchesSearch && matchesCategory;
    }
  );
};

interface ToolsHomeProps {
  globals: Globals
}

function ToolsHome (props: ToolsHomeProps) {
  const { globals } = props;

  const initialFilters : ToolFiltersState = { search: '', categoryIds: []};
  const [toolFiltersState, setToolFiltersState] = useState<ToolFiltersState>(initialFilters);

  const [tools, setTools] = useState<undefined | Tool[]>(undefined);
  const [showRefreshAlert, setShowRefreshAlert] = useState<undefined | boolean>(undefined);

  const { isLoading: isGetToolsLoading, error: getToolsError, data: getToolsData} = useQuery({
    retry: false,
    retryOnMount: false,
    staleTime: Infinity,
    queryKey: ['getTools'], 
    queryFn: async () => {
      return await getTools();
    },
  });

  useEffect(() => {
    if (getToolsData) {
      setTools(getToolsData);
    }
  }, [getToolsData]);

  const onToolUpdate = (newTool: Tool) => {
    /*
    Creates new array with newTool replacing its previous version;
    Uses function inside setState hook to handle overlapping requests
    */
    setTools((oldTools) => {
      if (oldTools === undefined) throw Error('Expected tools variable to be defined!');
      const newTools = oldTools.map(t => t.id === newTool.id ? newTool : t);
      return newTools;
    });

    if (showRefreshAlert === undefined) setShowRefreshAlert(true);
  };

  const handleRefreshAlertClose = () => setShowRefreshAlert(false);

  const isLoading = isGetToolsLoading;
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
    const [searchFilter, categoriesFilter] = [toolFiltersState.search, toolFiltersState.categoryIds];
    const filteredTools = searchFilter !== '' || categoriesFilter.length > 0 ? filterTools(tools, toolFiltersState) : tools;
    toolNumString = `${filteredTools.length} of ${tools.length}`;
    toolCardContainer = (
      <Grid container spacing={2} justifyContent='center'>
        {
          filteredTools.length > 0
            ? filteredTools.map(t => (
              <Grid item key={t.id}><ToolCard tool={t} onToolUpdate={onToolUpdate} /></Grid>
            ))
            : <Grid item><Alert severity='info'>No matching results</Alert></Grid>
        }
      </Grid>
    );
  }

  return (
    <div id='root'>
      <HeaderAppBar
        user={globals.user}
        helpURL={globals.help_url}
      />
      <MainContainer>
        <Typography variant='h6' component='h2' sx={{ textAlign: 'center', marginBottom: 3 }}>
          Instructor Tools is a collection of tools and resources to improve the online experience for you and your students.
        </Typography>
        {feedbackBlock}
        <Grid container sx={{ justifyContent: 'center', alignItems: 'center', gap:1}}>
          <Grid item>
            <Typography aria-live='polite' aria-atomic>{toolNumString} tools displayed. Type a search term or select categories to filter:</Typography>
          </Grid>
          <Grid item>
            { ( toolFiltersState.categoryIds.length > 0 || 
              toolFiltersState.search !== initialFilters.search) // show when a filter is applied
              &&
              (
                <Button
                  onClick={() => setToolFiltersState(initialFilters)}>
                    Clear All
                </Button>
              )
            }
          </Grid>

        </Grid>
        <ToolFilters 
          categoryIdsSelected={toolFiltersState.categoryIds}
          searchTerm={toolFiltersState.search}
          onSearchFilterChange={(v:string) => 
            setToolFiltersState(filters => ({
              ...filters, 
              search: v 
            }))
          }
          onCategoryIdsSelectedChange={(categoryIds: number[]) => 
            setToolFiltersState(filters => ({
              ...filters,
              categoryIds: categoryIds
            }))
          }
        />
        
        <div aria-describedby='tool-card-container-loading' aria-busy={isGetToolsLoading}>
          {toolCardContainer}
        </div>
      </MainContainer>
      <Typography component='footer' sx={{ textAlign: 'center' }}>
        Copyright © 2024 The Regents of the University of Michigan
      </Typography>
      <Snackbar open={showRefreshAlert} onClose={handleRefreshAlertClose} autoHideDuration={10000}>
        <Alert severity='info' elevation={2} onClose={handleRefreshAlertClose}>
          Refresh the page to update the tool&apos;s appearance in the {TOOL_MENU_NAME}.
        </Alert>
      </Snackbar>
    </div>
  );
}

export default ToolsHome;
