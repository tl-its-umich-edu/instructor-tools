import React, {useState} from 'react';
import SearchIcon from '@mui/icons-material/Search';
import ClearIcon from '@mui/icons-material/Clear';
import { AppBar, Button, Grid, InputBase, InputAdornment, IconButton, Paper, Toolbar, Typography } from '@mui/material';

import { User } from '../interfaces';

interface HeaderAppBarProps {
  onFilterChange: (v: string) => void
  user: User | null
  helpURL: string
}

export default function HeaderAppBar (props: HeaderAppBarProps) {
  const [filterValue, setFilterValue] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFilterValue(e.target.value);
    props.onFilterChange(e.target.value);
  };

  const handleClear = () => {
    setFilterValue('');
    props.onFilterChange('');
  };

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
                id='tool-filter'
                placeholder='Filter by name or description'
                aria-label='Filter tools by name or description'
                fullWidth
                value={filterValue}
                onChange={handleChange}
                endAdornment={
                  filterValue && (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="Clear filter"
                        onClick={handleClear}
                        edge="end"
                        size="small"
                      >
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  )
                }
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
