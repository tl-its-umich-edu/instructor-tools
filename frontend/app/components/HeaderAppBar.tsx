import React from 'react';
import { AppBar, Button, Grid, Toolbar, Typography } from '@mui/material';

import { User } from '../interfaces';

interface HeaderAppBarProps {
  onSearchFilterChange: (v: string) => void
  user: User | null
  helpURL: string
}

export default function HeaderAppBar (props: HeaderAppBarProps) {
  return (
    <AppBar position='sticky'>
      <Toolbar>
        <Grid container direction='row' alignItems='center'>
          <Grid item sm={5} xs={6}>
            <Typography variant='h5' component='h1'>
              Instructor Tools
            </Typography>
          </Grid>
        </Grid>
        <Grid item xs='auto' container justifyContent='space-around'>
          <Button color='inherit' target='_blank' href={props.helpURL}>Help</Button>
          {props.user?.is_staff && <Button color='inherit' href='/admin'>Admin</Button>}
        </Grid>
      </Toolbar>
    </AppBar>
  );
}
