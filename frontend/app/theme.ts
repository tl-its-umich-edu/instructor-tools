import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    primary: {
      main: '#00274C'
    },
    error: {
      main: '#E31C3D'
    },
    warning: {
      main: '#E2CF2A'
    },
    success: {
      main: '#306430'
    }
  },
  components: {
    MuiLink: {
      defaultProps: {
        underline: 'always'
      },
      styleOverrides: {
        root: {
          '&:hover': {
            color: '#9a3324'
          }
        }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: ({ theme }) => ({
          '&:focus-visible': {
            outline: `2px solid ${theme.palette.primary.main}`,
            outlineOffset: '2px',
          }
        })
      }
    },
  }
});

export default theme;