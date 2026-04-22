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
    MuiTypography: {
      defaultProps: {
        // https://mui.com/material-ui/react-typography/#changing-the-semantic-element
        variantMapping: {
          h3: 'h2',
          h4: 'h2',
          h5: 'h2',
          h6: 'h2',
        },
      },
    },
  }
});

export default theme;