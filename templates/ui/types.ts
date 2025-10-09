// UI data contracts (TypeScript interfaces)

export interface ComputationResult {
  valueA: number;
  valueB: number;
  formattedSummary: string; // e.g., "632.9e9 units"
  formula?: string;
}

export interface OptionItem {
  id: string;
  label: string;
  value: string; // normalized value used internally
}

export interface SelectorChangeEvent {
  value: string;
  id?: string;
}

export interface ApiError {
  code: string;
  message: string;
}

