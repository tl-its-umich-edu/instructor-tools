import React from 'react';
import SearchIcon from '@mui/icons-material/Search';
import { AppBar, Button, Grid, InputBase, Paper, Toolbar, Typography } from '@mui/material';

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
          <Grid
            item
            sm={6}
            xs={5}
            container
            justifyContent='flex-start'
            alignItems='center'
            component={Paper}
            variant='outlined'
            sx={{ paddingLeft: 1, paddingRight: 1, paddingTop: 0.5, paddingBottom: 0.5 }}
          >
            <Grid item xs='auto'>
              <SearchIcon sx={{ marginRight: 1 }} />
            </Grid>
            <Grid item xs>
              <InputBase
                id='tool-search-filter'
                placeholder='Filter by name or description'
                aria-label='Filter tools by name or description'
                fullWidth
                type='search'
                onChange={(e) => props.onSearchFilterChange(e.target.value)}
              />
            </Grid>
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
