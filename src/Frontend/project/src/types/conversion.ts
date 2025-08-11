export type ConversionStatus = 'idle' | 'processing' | 'success' | 'error';

export interface ConversionResult {
  html: string;
  title?: string;
  accessibilityScore?: number;
  warnings?: string[];
  metadata?: {
    filename: string;
    size: number;
    tesseract_used: boolean;
  };
}