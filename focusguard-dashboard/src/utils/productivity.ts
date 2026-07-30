/**
 * Productivity normalization utilities
 * Handles various backend enum formats for productivity classification
 */

export type ProductivityValue = 'PRODUCTIVE' | 'NON_PRODUCTIVE' | 'NEUTRAL' | null;

/**
 * Normalizes productivity values from various backend formats
 * 
 * Handles:
 * - Plain enum values: "PRODUCTIVE", "NEUTRAL", "NON_PRODUCTIVE"
 * - Full enum paths: "ProductivityClassification.PRODUCTIVE", etc.
 * - Case-insensitive matching
 * 
 * @param value - The productivity value from the backend
 * @returns Normalized productivity value or null if invalid
 * 
 * @example
 * normalizeProductivity("PRODUCTIVE") // "PRODUCTIVE"
 * normalizeProductivity("ProductivityClassification.PRODUCTIVE") // "PRODUCTIVE"
 * normalizeProductivity("productive") // "PRODUCTIVE"
 * normalizeProductivity(null) // null
 * normalizeProductivity("") // null
 */
export function normalizeProductivity(value: string | null | undefined): ProductivityValue {
  if (!value || value.trim() === '') {
    return null;
  }

  // Strip enum prefix if present (e.g., "ProductivityClassification.PRODUCTIVE" -> "PRODUCTIVE")
  const normalized = value.includes('.') 
    ? value.split('.').pop()?.trim() 
    : value.trim();

  if (!normalized) {
    return null;
  }

  // Case-insensitive matching
  const upperNormalized = normalized.toUpperCase();

  switch (upperNormalized) {
    case 'PRODUCTIVE':
      return 'PRODUCTIVE';
    case 'NON_PRODUCTIVE':
      return 'NON_PRODUCTIVE';
    case 'NEUTRAL':
      return 'NEUTRAL';
    default:
      // Handle unexpected values gracefully
      return null;
  }
}

/**
 * Gets the badge color class for a productivity value
 * @param value - The productivity value (normalized or raw)
 * @returns Tailwind CSS class string
 */
export function getProductivityBadgeColor(value: string | null | undefined): string {
  const normalized = normalizeProductivity(value);

  switch (normalized) {
    case 'PRODUCTIVE':
      return 'bg-green-100 text-green-800';
    case 'NEUTRAL':
      return 'bg-yellow-100 text-yellow-800';
    case 'NON_PRODUCTIVE':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Gets the display label for a productivity value
 * @param value - The productivity value (normalized or raw)
 * @returns Human-readable label
 */
export function getProductivityLabel(value: string | null | undefined): string {
  const normalized = normalizeProductivity(value);

  switch (normalized) {
    case 'PRODUCTIVE':
      return 'Productive';
    case 'NEUTRAL':
      return 'Neutral';
    case 'NON_PRODUCTIVE':
      return 'Non-Productive';
    default:
      return 'Not Available';
  }
}
