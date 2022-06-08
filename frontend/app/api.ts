import Cookies from 'js-cookie';

import { Tool } from './interfaces';

export const getCSRFToken = (): string | undefined => Cookies.get('csrftoken');

const API_BASE = '/api';
const JSON_MIME_TYPE = 'application/json';

const BASE_MUTATION_HEADERS: HeadersInit = {
  Accept: JSON_MIME_TYPE,
  'Content-Type': JSON_MIME_TYPE,
  'X-Requested-With': 'XMLHttpRequest'
};

const createErrorMessage = async (res: Response): Promise<string> => {
  let errorBody;
  try {
    errorBody = await res.json();
  } catch {
    console.error('Error body was not JSON.');
    errorBody = undefined;
  }
  return (
    'Error occurred! ' +
    `Status: ${res.status}${res.statusText !== '' ? ' ' + res.statusText : ''}` +
    (errorBody !== undefined ? '; Body: ' + JSON.stringify(errorBody) : '.')
  );
};

async function getTools (): Promise<Tool[]> {
  const url = `${API_BASE}/lti_tools/`;
  const res = await fetch(url);
  if (!res.ok) {
    console.error(res);
    throw new Error(await createErrorMessage(res));
  }
  const data: Tool[] = await res.json();
  return data;
}

async function updateToolNav (canvas_tool_id: number, navEnabled: boolean): Promise<void> {
  const body = { navigation_enabled: navEnabled };
  const url = `${API_BASE}/lti_tools/${canvas_tool_id}/`;
  const requestInit: RequestInit = {
    method: 'PUT',
    body: JSON.stringify(body),
    headers: {
      ...BASE_MUTATION_HEADERS,
      'X-CSRFTOKEN': getCSRFToken() ?? '' // Could throw error?
    }
  };
  const res = await fetch(url, requestInit);
  if (!res.ok) throw new Error(await createErrorMessage(res));
  return;
}

export { getTools, updateToolNav };
