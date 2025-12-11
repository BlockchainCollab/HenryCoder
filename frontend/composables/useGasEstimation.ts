/**
 * useGasEstimation Composable
 * Manages gas estimation state and API calls
 */

import { ref, computed, watch, type Ref } from 'vue';
import { fetchGasAnnotations } from '@/lib/gas-api';
import {
  createGasLineAnnotations,
  type GasAnnotatedResponse,
  type GasLineAnnotations,
} from '@/lib/gas-types';

export interface UseGasEstimationOptions {
  /**
   * The Ralph code to estimate gas for
   */
  code: Ref<string>;
  
  /**
   * API base URL
   */
  apiBase: string;
  
  /**
   * Whether gas estimation is enabled
   */
  enabled?: Ref<boolean>;
  
  /**
   * Debounce delay in ms before fetching (default: 1000)
   */
  debounceMs?: number;
  
  /**
   * Optional map from original line numbers to clean line numbers.
   * Used when annotation lines (// @@@) are removed from display.
   */
  originalToCleanLineMap?: Ref<Map<number, number>>;
}

export interface UseGasEstimationReturn {
  /**
   * Whether gas estimation is loading
   */
  loading: Ref<boolean>;
  
  /**
   * Error message if estimation failed
   */
  error: Ref<string | null>;
  
  /**
   * Full gas estimation response
   */
  response: Ref<GasAnnotatedResponse | null>;
  
  /**
   * Line-indexed gas annotations for gutter display
   */
  lineAnnotations: Ref<GasLineAnnotations>;
  
  /**
   * Whether there are any gas annotations
   */
  hasAnnotations: Ref<boolean>;
  
  /**
   * Manually trigger gas estimation
   */
  estimate: () => Promise<void>;
  
  /**
   * Clear gas estimation data
   */
  clear: () => void;
  
  /**
   * Update line annotations with a new line mapping
   */
  updateLineMapping: (lineMap: Map<number, number>) => void;
}

export function useGasEstimation(
  options: UseGasEstimationOptions
): UseGasEstimationReturn {
  const { 
    code, 
    apiBase, 
    enabled = ref(true), 
    debounceMs = 1000,
    originalToCleanLineMap = ref(new Map()),
  } = options;

  // State
  const loading = ref(false);
  const error = ref<string | null>(null);
  const response = ref<GasAnnotatedResponse | null>(null);
  const lineAnnotations = ref<GasLineAnnotations>(new Map());
  const currentLineMap = ref<Map<number, number>>(new Map());

  // Computed
  const hasAnnotations = computed(() => lineAnnotations.value.size > 0);

  // Debounce timer
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  /**
   * Update line annotations based on the current response and line mapping
   */
  function updateLineAnnotationsFromResponse(): void {
    if (response.value) {
      lineAnnotations.value = createGasLineAnnotations(
        response.value, 
        currentLineMap.value
      );
    }
  }

  /**
   * Update line mapping and recalculate annotations
   */
  function updateLineMapping(lineMap: Map<number, number>): void {
    currentLineMap.value = lineMap;
    updateLineAnnotationsFromResponse();
  }

  /**
   * Fetch gas estimation from API
   */
  async function estimate(): Promise<void> {
    const codeValue = code.value;
    
    // Skip if disabled or no code
    if (!enabled.value || !codeValue?.trim()) {
      clear();
      return;
    }

    // Skip if code is too short (likely incomplete)
    if (codeValue.length < 50) {
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      const result = await fetchGasAnnotations(codeValue, apiBase);
      response.value = result;
      // Use the current line map when creating annotations
      lineAnnotations.value = createGasLineAnnotations(result, currentLineMap.value);
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Gas estimation failed';
      console.error('Gas estimation error:', e);
    } finally {
      loading.value = false;
    }
  }

  /**
   * Clear all gas estimation data
   */
  function clear(): void {
    response.value = null;
    lineAnnotations.value = new Map();
    error.value = null;
  }

  /**
   * Debounced estimation
   */
  function debouncedEstimate(): void {
    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(() => {
      estimate();
    }, debounceMs);
  }

  // Watch for code changes and trigger estimation
  watch(
    code,
    (newCode, oldCode) => {
      // Only estimate if code changed significantly
      if (newCode !== oldCode && enabled.value) {
        debouncedEstimate();
      }
    },
    { immediate: false }
  );

  // Watch enabled state
  watch(enabled, (isEnabled) => {
    if (!isEnabled) {
      clear();
    } else if (code.value) {
      debouncedEstimate();
    }
  });

  return {
    loading,
    error,
    response,
    lineAnnotations,
    hasAnnotations,
    estimate,
    clear,
    updateLineMapping,
  };
}
