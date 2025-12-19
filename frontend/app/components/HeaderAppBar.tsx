import React from 'react';
import { AppBar, Breadcrumbs, Button, Grid, Toolbar, Typography } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import Link from '@mui/material/Link';
import { User } from '../interfaces';

interface HeaderAppBarProps {
  user: User | null;
  helpURL: string;
  breadcrumbTitle?: string; // when provided render breadcrumb: Home link + breadcrumbTitle
}

export default function HeaderAppBar (props: HeaderAppBarProps) {
  const { user, helpURL, breadcrumbTitle } = props;

  const renderTitle = () => {
    if (breadcrumbTitle) {
      return (
        <Breadcrumbs color='inherit' aria-label="breadcrumb">
          <Link
            variant='h5'
            component={RouterLink}
            to='/'
            underline="hover"
            sx={{ color: 'inherit', textDecoration: 'none', display: 'inline-block', marginRight: 1 }}
          >
            Instructor Tools
          </Link>
          <Typography variant='h5' component='span' sx={{ display: 'inline-block' }}>
            {breadcrumbTitle}
          </Typography>
        </Breadcrumbs>
      );
    }

    return (
      <Typography variant='h5'>
        Instructor Tools
      </Typography>
    );
  };

  return (
    <AppBar position='sticky'>
      <Toolbar>
        <Grid container direction='row' alignItems='center'>
          <Grid item>
            {renderTitle()}
          </Grid>
        </Grid>
        <Grid item xs='auto' container justifyContent='space-around'>
          <Button color='inherit' target='_blank' href={helpURL}>Help</Button>
          {user?.is_staff && <Button color='inherit' href='/admin'>Admin</Button>}
        </Grid>
      </Toolbar>
    </AppBar>
  );
}
