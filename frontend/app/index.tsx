import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

import { Globals } from './interfaces';
import { SIGNED_PAYLOAD_STORAGE_KEY } from './constants';
import theme from './theme';
import { ConsentManagerProvider } from './components/ConsentManagerProvider';
import App from './App';

const globalsId = 'cae_globals';
const globalsEl = document.getElementById(globalsId);
if (globalsEl === null) throw Error(`"${globalsId}" was not found!`);
if (globalsEl.textContent === null) throw Error(`No text content in "${globalsId}"!`);
const globals: Globals = Object.freeze(JSON.parse(globalsEl.textContent));

if (globals.signed_course_user_payload !== null) {
  sessionStorage.setItem(SIGNED_PAYLOAD_STORAGE_KEY, globals.signed_course_user_payload);
}else {
  throw Error('signed_course_user_payload is null in globals!');
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  }
});

const router = createBrowserRouter([
  { path: '/*', element: <App globals={globals} /> }
]);

const container = document.getElementById('react-app');
if (container === null) throw Error('"react-app" was not found!');
const root = createRoot(container);

root.render(
  <QueryClientProvider client={queryClient}>
    <ThemeProvider theme={theme}>
      <ConsentManagerProvider globals={globals}>
        <RouterProvider router={router} />
      </ConsentManagerProvider>
    </ThemeProvider>
  </QueryClientProvider>
);
