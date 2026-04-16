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
      defaultProps: {
        disableFocusRipple: true,
      },
      styleOverrides: {
        root: ({ theme }) => ({
          '&:focus-visible': {
            boxShadow: `0 0 0 2px ${theme.palette.common.white}, 0 0 0 4px ${theme.palette.primary.main}`,
          }, 
        })
      }
    },
    MuiButtonBase: {
      defaultProps: {
        disableRipple: true,
      },
    }
  }
});

export default theme;