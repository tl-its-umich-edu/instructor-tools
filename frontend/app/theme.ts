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
    }
  }
});

export default theme;