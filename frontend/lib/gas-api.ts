/**
 * Gas Estimation API Functions
 * Handles communication with the backend gas estimation endpoints
 */

import type { GasAnnotatedResponse } from './gas-types';

/**
 * Fetch gas estimates with line annotations for gutter display
 */
export async function fetchGasAnnotations(
  ralph_code: string,
  apiBase: string
): Promise<GasAnnotatedResponse> {
  const response = await fetch(`${apiBase}/gas/estimate/annotated`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ralph_code }),
  });

  if (!response.ok) {
    const errorData = await response
      .json()
      .catch(() => ({ detail: 'Gas estimation failed' }));
    throw new Error(errorData.detail || 'Gas estimation failed');
  }

  return response.json();
}

/**
 * Fetch gas constants from the API
 */
export async function fetchGasConstants(apiBase: string): Promise<Record<string, any>> {
  const response = await fetch(`${apiBase}/gas/constants`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch gas constants');
  }

  return response.json();
}
