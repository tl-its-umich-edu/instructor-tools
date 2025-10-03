import { ToolCategory } from '../interfaces';
import { useQuery } from '@tanstack/react-query';
import { getCategories } from '../api';
import React from 'react';
import { Alert, Box, Chip, CircularProgress, Grid } from '@mui/material';
import DoneIcon from '@mui/icons-material/Done';
import ErrorsDisplay from './ErrorsDisplay';

interface CategoriesSelectorProps {
    categoryIdsSelected: Set<number>,
    onCategoryIdsSelectedChange: (categoryIds: Set<number>) => void
}

const CategoriesSelector = ({ categoryIdsSelected, onCategoryIdsSelectedChange }: CategoriesSelectorProps) => {
  const { data: categories, isLoading: getCategoriesLoading, error: getCategoriesError } = useQuery({
    queryKey: ['getCategories'],
    queryFn: getCategories,
  });
  const errors = [getCategoriesError].filter(e => e !== null) as Error[];

  const handleCategoryToggle = (categoryId: number) => {
    const newSelected = new Set(categoryIdsSelected);
    if (newSelected.has(categoryId)) {
      newSelected.delete(categoryId);
    } else {
      newSelected.add(categoryId);
    }
    onCategoryIdsSelectedChange(newSelected);
  };


  return (
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
        <Grid container justifyContent='center' sx={{ marginBottom: 2 }} >
          { categories && categories.length > 0 ? (
            categories.map((category:ToolCategory) => (
              <Grid item key={`category-chip-${category.id}`}>
                <Chip
                  label={category.category_name}
                  color={categoryIdsSelected.has(category.id) ? 'primary' : 'default'}
                  variant={categoryIdsSelected.has(category.id) ? 'filled' : 'outlined'}
                  onClick={() => handleCategoryToggle(category.id)}
                  onDelete={categoryIdsSelected.has(category.id) ? () => handleCategoryToggle(category.id) : undefined}
                  deleteIcon={<DoneIcon />}
                  sx={{ margin: 0.5 }}
                />
              </Grid>
            ))
          ) : (
            <Grid item>
              <Alert severity='info'> No tool categories found</Alert>
            </Grid>
          )}
        </Grid>
      }
    </Grid>
  );
};

export default CategoriesSelector;