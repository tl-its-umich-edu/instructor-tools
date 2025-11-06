import { Box, Button } from '@mui/material';
import React from 'react';
import usePromise from '../hooks/usePromise';
import { updateAltTextStartSync } from '../api';
import ErrorsDisplay from './ErrorsDisplay';
import { ArrowBack } from '@mui/icons-material';

function AltTextHome () {
  const [startSync, isStartSyncLoading, startSyncError] = usePromise(
    async () => await updateAltTextStartSync(),
    () => console.log('Start sync initiated!')
  );
  
  return (
    <Box>
      <Button
        variant='outlined'
        startIcon={<ArrowBack/>}
        href='../'
      >
        Go Back
      </Button>
      <p>Alt Text Helper Home</p>
      <Button 
        onClick={() => startSync()}
        variant='contained'
        disabled={isStartSyncLoading}
      >
        Start Sync
      </Button>
      { startSyncError && 
        <Box sx={{ marginBottom: 1 }}>
          <ErrorsDisplay errors={[startSyncError]} />
        </Box>
      }
    </Box>
  );
}

export default AltTextHome;