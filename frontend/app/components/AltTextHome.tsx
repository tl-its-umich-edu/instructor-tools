import { Box, Button } from '@mui/material';
import React, { useState } from 'react';
import { updateAltTextStartSync } from '../api';
import ErrorsDisplay from './ErrorsDisplay';
import ArrowBack from '@mui/icons-material/ArrowBack';
import { Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Globals, SyncTask } from '../interfaces';

interface AltTextHomeProps {
  globals: Globals
}

function AltTextHome(props: AltTextHomeProps) {
  const { course_id } = props.globals;
  const [syncTask, setSyncTask] = useState<SyncTask | null>(null);

  const {
    mutate: doStartSync,
    error: startSyncError,
    isError: isStartSyncError,
    isPending: startSyncPending
  } = useMutation({
    mutationFn: async () => {
      const response = await updateAltTextStartSync({
        courseId: course_id
      });
      return response;
    },
    onSuccess: (data) => {
      setSyncTask(data);
    },
    onError: (error) => {
      console.error('Error starting sync:', error);
    }
  });

  return (
    <Box>
      <Button
        variant='outlined'
        startIcon={<ArrowBack />}
        component={Link}
        to={'../'}
      >
        Go Back
      </Button>
      <p>Alt Text Helper Home</p>
      <Button
        onClick={() => doStartSync()}
        variant='contained'
        disabled={startSyncPending}
      >
        Start Sync
      </Button>
      {syncTask &&
        <p>Task ID: {syncTask.id}</p>
      }
      {isStartSyncError &&
        <Box sx={{ marginBottom: 1 }}>
          <ErrorsDisplay errors={[startSyncError].filter(e => e !== null) as Error[]} />
        </Box>
      }
    </Box>
  );
}

export default AltTextHome;