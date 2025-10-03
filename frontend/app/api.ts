import Cookies from 'js-cookie';

import { Tool, ToolCategory } from './interfaces';

const API_BASE = '/api';
const JSON_MIME_TYPE = 'application/json';

const BASE_MUTATION_HEADERS: HeadersInit = {
  Accept: JSON_MIME_TYPE,
  'Content-Type': JSON_MIME_TYPE,
  'X-Requested-With': 'XMLHttpRequest'
};

const getCSRFToken = (): string | undefined => Cookies.get('csrftoken');

const createErrorMessage = async (res: Response): Promise<string> => {
  let errorBody: Record<string, unknown> | undefined;
  try {
    errorBody = await res.json();
  } catch {
    console.error('Error body was not JSON.');
    errorBody = undefined;
  }

  let message;
  if (errorBody !== undefined) {
    if ('message' in errorBody && typeof errorBody.message === 'string')
      message = ' Message: ' + errorBody.message;
    else {
      message = `Error Body: ${JSON.stringify(errorBody)}`;
    }
  }

  return (
    'Error occurred! ' +
    `Status: ${res.status}` + (res.statusText !== '' ? ` (${res.statusText})` : '') +
    (message !== undefined ? '; ' + message : '.')
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

interface UpdateToolNavData {
  canvasToolId: number
  navEnabled: boolean
}

async function updateToolNav (data: UpdateToolNavData): Promise<void> {
  const { canvasToolId, navEnabled } = data;
  const body = { navigation_enabled: navEnabled };
  const url = `${API_BASE}/lti_tools/${canvasToolId}/`;
  const requestInit: RequestInit = {
    method: 'PUT',
    body: JSON.stringify(body),
    headers: {
      ...BASE_MUTATION_HEADERS,
      'X-CSRFTOKEN': getCSRFToken() ?? ''
    }
  };
  const res = await fetch(url, requestInit);
  if (!res.ok) {
    console.error(res);
    throw new Error(await createErrorMessage(res));
  }
  return;
}

async function getCategories (): Promise<ToolCategory[]> {
  const url = `${API_BASE}/tool_categories/`;
  const res = await fetch(url);
  if (!res.ok) {
    console.error(res);
    throw new Error(await createErrorMessage(res));
  }
  const data: ToolCategory[] = await res.json();
  return data;
}

export { getTools, updateToolNav, getCategories };
