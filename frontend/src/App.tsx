import { createTheme, ThemeProvider, CssBaseline } from '@mui/material';
import ResumeForm from './components/ResumeForm';

const theme = createTheme({
  palette: {
    primary: {
      main: '#3498db',
    },
    background: {
      default: '#f5f5f5'
    }
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ResumeForm />
    </ThemeProvider>
  );
}

export default App;