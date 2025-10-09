import { useQuery } from '@tanstack/react-query';
import { getCategories } from '../api';
import React from 'react';
import { Box, Chip, CircularProgress, FormControl, Grid, InputLabel, MenuItem, OutlinedInput, Select, SelectChangeEvent } from '@mui/material';
import ErrorsDisplay from './ErrorsDisplay';
import { styled } from '@mui/material/styles';

interface CategoriesSelectorProps {
    categoryIdsSelected: number[],
    onCategoryIdsSelectedChange: (categoryIds: number[]) => void
}
const PREFIX = 'CategoriesSelector';
const classes = {
  select: `${PREFIX}-Select`,
  box: `${PREFIX}-Box`,
  chip: `${PREFIX}-Chip`
};

const SelectorContainer = styled('div')(({ theme }) => ({
  marginBottom: theme.spacing(2),
  [`& .${classes.select}`]: {
    textAlign: 'center',
    width: 450,
  },

  [`& .${classes.box}`]: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 0.5
  },

  [`& .${classes.chip}`]: {
    margin: 2
  }

}));

const MenuProps = {
  PaperProps: {
    style: {
      maxHeight:'40%'
    },
  }
};

const CategoriesSelector = ({ categoryIdsSelected, onCategoryIdsSelectedChange }: CategoriesSelectorProps) => {
  const { data: categories, isLoading: getCategoriesLoading, error: getCategoriesError } = useQuery({
    queryKey: ['getCategories'],
    queryFn: getCategories,
  });
  const errors = [getCategoriesError].filter(e => e !== null) as Error[];

  const handleChange = (event: SelectChangeEvent<number[]>) => {
    const {
      target: { value },
    } = event;
    if (typeof value !== 'string') {
      onCategoryIdsSelectedChange(value as number[]);
    }
  };

  return (
    <SelectorContainer>
      <Grid 
        container
        direction='column'
        alignItems='center'>
        { getCategoriesLoading && 
        <div aria-describedby='categories-loading' aria-busy={getCategoriesLoading}>
          <CircularProgress />
        </div>}
        { errors.length > 0 && 
        <Box sx={{ marginBottom: 1 }}>
          <ErrorsDisplay errors={errors} />
        </Box>
        }
        {
          <FormControl>
            <InputLabel id="category-select-label">Categories Selected</InputLabel>
            <Select
              labelId="category-select-label"
              id="category-select"
              className={classes.select}
              multiple
              value={categoryIdsSelected}
              onChange={handleChange}
              input={<OutlinedInput id="select-multiple-categories" label="Select Categories" />}
              renderValue={(selectedIds) => (
                <Box className={classes.box}>
                  {
                    categories?.map(
                      (category) => (
                        <>
                          {selectedIds.includes(category.id) && (
                            <Chip 
                              key={category.id} 
                              className={classes.chip}
                              label={category.category_name}/>
                          )}
                        </>
                      )
                    )}
                </Box>
              )}
              MenuProps={MenuProps}
            >
              {categories?.map((category) => (
                <MenuItem
                  key={category.id}
                  value={category.id}
                >
                  {category.category_name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        }
      </Grid>
    </SelectorContainer>
  );
};

export default CategoriesSelector;