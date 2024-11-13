import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from 'react-query';
import { ThemeProvider } from '@mui/material';

import Home from './components/Home';
import { Globals } from './interfaces';
import theme from './theme';

const globalsId = 'cae_globals';
const globalsEl = document.getElementById(globalsId);
if (globalsEl === null) throw Error(`"${globalsId}" was not found!`);
if (globalsEl.textContent === null) throw Error(`No text content in "${globalsId}"!`);
const globals: Globals = Object.freeze(JSON.parse(globalsEl.textContent));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      retryOnMount: false,
      staleTime: Infinity
    },
    mutations: { retry: false }
  }
});

const container = document.getElementById('react-app');
if (container === null) throw Error('"react-app" was not found!');
const root = createRoot(container);

root.render(
  <QueryClientProvider client={queryClient}>
    <ThemeProvider theme={theme}>
      <Home globals={globals} />
    </ThemeProvider>
  </QueryClientProvider>
);
