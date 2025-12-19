import { Box, Checkbox, Chip, CircularProgress, FormControl, Grid, InputLabel, ListItemText, MenuItem, OutlinedInput, Select, SelectChangeEvent, styled, TextField } from '@mui/material';
import React from 'react';
import { getCategories } from '../api';
import { useQuery } from '@tanstack/react-query';
import { ToolCategory } from '../interfaces';
import FilterList from '@mui/icons-material/FilterList';

const MAX_CHIPS_SHOWN = 5; // for category chips overflow
const PREFIX = 'ToolFilters';
const classes = {
  select: `${PREFIX}-Select`,
  filterBox: `${PREFIX}-FilterBox`,
  chip: `${PREFIX}-Chip`,
  chipBox: `${PREFIX}-ChipBox`
};

const ToolFiltersContainer = styled('div')(({ theme }) => ({
  [`& .${classes.filterBox}`]: {
    paddingLeft: theme.spacing(4),
    paddingRight: theme.spacing(3),
    maxWidth: 700,
    margin: 'auto', 
    paddingTop: theme.spacing(2),
    paddingBottom: theme.spacing(2),
  },
  [`& .${classes.chipBox}`]: {
    display: 'flex',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: theme.spacing(1),
    padding: theme.spacing(0.5),
    justifyContent: 'center'
  }
}));

const MenuProps = {
  PaperProps: {
    style: {
      maxHeight:'40%'
    },
  }
};

interface ToolFiltersProps {
    categoryIdsSelected: number[],
    searchTerm:string,
    onSearchFilterChange:(searchTerm: string) => void
    onCategoryIdsSelectedChange:(categoryIds: number[]) => void
}

function ToolFilters({
  categoryIdsSelected,
  searchTerm,
  onSearchFilterChange, 
  onCategoryIdsSelectedChange 
}: ToolFiltersProps) {
  const { data: categories = [], isLoading: getCategoriesLoading } = useQuery<ToolCategory[]>({
    queryKey: ['getCategories'],
    queryFn: getCategories,
  });

  const handleCategoryChange = (event: SelectChangeEvent<number[]>) => {
    const {
      target: { value },
    } = event;
    const newCategoryIdsSelected = value as number[];
    onCategoryIdsSelectedChange(newCategoryIdsSelected);
  };
  const handleChipDelete = (idToDelete: number) => {
    const newSelectedIds = categoryIdsSelected.filter((id) => id !== idToDelete);
    onCategoryIdsSelectedChange(newSelectedIds);
  };

  const categoriesSelected = categories.filter((cat) => categoryIdsSelected.includes(cat.id));
  const categoriesInputDisplay = categoriesSelected.map((cat) => cat.category_name).join(', ');
  const chipsToShow = categoriesSelected.slice(0, MAX_CHIPS_SHOWN);
  const hiddenCount = categoriesSelected.length - MAX_CHIPS_SHOWN;

  return (
    <ToolFiltersContainer>
      {categoryIdsSelected.length > 0 && (
        <Box className={classes.chipBox}>
          {chipsToShow.map((category) => (
            <Chip
              key={category.id}
              label={category.category_name}
              onDelete={() => handleChipDelete(category.id)}
            />
          ))}
          {hiddenCount > 0 && (
            <Chip
              label={`+ ${hiddenCount} more`}
              title={categoriesInputDisplay}
            />
          )}
        </Box>
      )}
      <Box className={classes.filterBox}>
        <Grid
          container
          spacing={2}
          alignItems="center"
        >
          <Grid item xs={12} sm={8}>
            <TextField
              fullWidth
              label='Filter by name or description'
              variant="outlined"
              id='tool-search-filter'
              type='search'
              value={searchTerm}
              onChange={(e) => onSearchFilterChange(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} sm={4}>
            { getCategoriesLoading && 
                <CircularProgress id='categories-loading' />
            }
            <div aria-describedby='categories-loading' aria-busy={getCategoriesLoading}>
              { !getCategoriesLoading && 
                <FormControl fullWidth>
                  <InputLabel id="category-select-label">Categories Selected</InputLabel>
                  <Select
                    labelId="category-select-label"
                    id="category-select"
                    className={classes.select}
                    multiple
                    value={categoryIdsSelected}
                    onChange={handleCategoryChange}
                    MenuProps={MenuProps}
                    input={<OutlinedInput id="select-multiple-categories" label="Select Categories" />}
                    renderValue={() => categoriesInputDisplay}
                    title={categoriesInputDisplay}
                    IconComponent={FilterList}
                  >
                    {categories.map((category) => (
                      <MenuItem
                        key={category.id}
                        value={category.id}
                      >
                        <Checkbox checked={categoryIdsSelected.includes(category.id)} />
                        <ListItemText primary={category.category_name} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              }
            </div>
          </Grid>
        </Grid>
      </Box>
    </ToolFiltersContainer>
  );
}
export default ToolFilters;