import React from 'react';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import LaunchIcon from '@mui/icons-material/Launch';
import { Button, ButtonProps } from '@mui/material';

function AddToolButton (props: ButtonProps) {
  return (
    <Button
      aria-label='Enable tool in course'
      variant='contained'
      startIcon={<AddIcon />}
      {...props}
    >
      Enable
    </Button>
  );
}

function RemoveToolButton (props: ButtonProps) {
  return (
    <Button
      aria-label='Disable tool in course'
      variant='outlined'
      startIcon={<RemoveIcon />}
      {...props}
    >
      Disable
    </Button>
  );
}

function LaunchToolButton (props: ButtonProps) {
  return (
    <Button
      aria-label='Launch tool with link'
      variant='outlined'
      startIcon={<LaunchIcon />}
      {...props}
    >
      Launch
    </Button>
  );
}

export { AddToolButton, RemoveToolButton, LaunchToolButton };
