import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material';

import { Globals } from './interfaces';
import theme from './theme';
import { ConsentManagerProvider } from './components/ConsentManagerProvider';
import App from './App';

const globalsId = 'cae_globals';
const globalsEl = document.getElementById(globalsId);
if (globalsEl === null) throw Error(`"${globalsId}" was not found!`);
if (globalsEl.textContent === null) throw Error(`No text content in "${globalsId}"!`);
const globals: Globals = Object.freeze(JSON.parse(globalsEl.textContent));

const queryClient = new QueryClient();

const container = document.getElementById('react-app');
if (container === null) throw Error('"react-app" was not found!');
const root = createRoot(container);

root.render(
  <QueryClientProvider client={queryClient}>
    <ThemeProvider theme={theme}>
      <ConsentManagerProvider globals={globals}>
        <App globals={globals} />
      </ConsentManagerProvider>
    </ThemeProvider>
  </QueryClientProvider>
);
