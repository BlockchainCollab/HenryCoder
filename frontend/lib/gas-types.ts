/**
 * Gas Estimation Types
 * Matches backend API response structures
 */

export interface GasOperationBreakdown {
  operation: string;
  count: number;
  gas_cost: number;
}

export interface GasFunctionAnnotation {
  function_name: string;
  start_line: number;
  end_line: number;
  total_gas: number;
  raw_gas: number;
  estimated_cost_alph: number;
  breakdown: GasOperationBreakdown[];
  warnings: string[];
}

export interface GasAnnotationSummary {
  total_functions: number;
  average_gas: number;
  most_expensive_function: string | null;
  most_expensive_gas: number;
}

export interface GasAnnotatedResponse {
  annotations: GasFunctionAnnotation[];
  summary: GasAnnotationSummary;
  gas_price_nanoalph: number;
  minimal_gas: number;
}

/**
 * Map of line numbers to gas annotations
 * Used for gutter decoration rendering
 */
export type GasLineAnnotations = Map<number, GasFunctionAnnotation>;

/**
 * Convert API response to line-indexed map for efficient lookup.
 * Optionally adjusts line numbers based on removed annotation lines.
 * 
 * @param response - The gas estimation API response
 * @param originalToCleanLineMap - Optional map from original line numbers to clean line numbers
 *                                  (after // @@@ annotation lines are removed)
 */
export function createGasLineAnnotations(
  response: GasAnnotatedResponse,
  originalToCleanLineMap?: Map<number, number>
): GasLineAnnotations {
  const map = new Map<number, GasFunctionAnnotation>();
  
  for (const annotation of response.annotations) {
    // If we have a line mapping, adjust the line number
    let targetLine = annotation.start_line;
    
    if (originalToCleanLineMap && originalToCleanLineMap.size > 0) {
      // Find the closest mapped line (in case the exact line isn't in the map)
      const mappedLine = originalToCleanLineMap.get(annotation.start_line);
      if (mappedLine !== undefined) {
        targetLine = mappedLine;
      } else {
        // Fallback: calculate based on how many lines were removed before this line
        let removedBefore = 0;
        for (const [origLine] of originalToCleanLineMap) {
          if (origLine < annotation.start_line) {
            // Count gaps - if original line 5 maps to clean line 4, 1 line was removed before it
          }
        }
        // Simple approach: count entries in map that are less than start_line
        // The difference between original and clean tells us offset
        let closestOriginal = 0;
        let closestClean = 0;
        for (const [orig, clean] of originalToCleanLineMap) {
          if (orig <= annotation.start_line && orig > closestOriginal) {
            closestOriginal = orig;
            closestClean = clean;
          }
        }
        if (closestOriginal > 0) {
          const offset = closestOriginal - closestClean;
          targetLine = annotation.start_line - offset;
        }
      }
    }
    
    // Map to the adjusted line number
    map.set(targetLine, {
      ...annotation,
      start_line: targetLine, // Update the annotation with adjusted line
    });
  }
  
  return map;
}

/**
 * Format gas cost for display
 */
export function formatGas(gas: number): string {
  if (gas >= 1_000_000) {
    return `${(gas / 1_000_000).toFixed(2)}M`;
  }
  if (gas >= 1_000) {
    return `${(gas / 1_000).toFixed(1)}K`;
  }
  return gas.toString();
}

/**
 * Format ALPH cost for display
 */
export function formatAlph(alph: number): string {
  if (alph < 0.000001) {
    return `<0.000001`;
  }
  if (alph < 0.001) {
    return alph.toFixed(6);
  }
  if (alph < 1) {
    return alph.toFixed(4);
  }
  return alph.toFixed(2);
}

/**
 * Get color class based on gas cost relative to minimum
 */
export function getGasCostColor(totalGas: number, minimalGas: number = 20_000): string {
  const ratio = totalGas / minimalGas;
  
  if (ratio <= 1.5) {
    return 'text-green-400'; // Low cost
  }
  if (ratio <= 3) {
    return 'text-yellow-400'; // Medium cost
  }
  if (ratio <= 5) {
    return 'text-orange-400'; // High cost
  }
  return 'text-red-400'; // Very high cost
}
