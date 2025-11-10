import React from 'react';
import AddIcon from '@mui/icons-material/Add';
import RemoveIcon from '@mui/icons-material/Remove';
import LaunchIcon from '@mui/icons-material/Launch';
import { Button, ButtonProps } from '@mui/material';
import StartIcon from '@mui/icons-material/Start';
import { Link } from 'react-router-dom';

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

function TryInternalToolButton (props: ButtonProps & { url: string }) {
  const { url, ...remainingProps } = props;
  return (
    <Button
      aria-label='Open internal tool'
      variant='contained'
      startIcon={<StartIcon/>}
      component={Link}
      to={url}
      {...remainingProps}
    >
      Try It Out
    </Button>
  );
}

export { AddToolButton, RemoveToolButton, LaunchToolButton, TryInternalToolButton};
