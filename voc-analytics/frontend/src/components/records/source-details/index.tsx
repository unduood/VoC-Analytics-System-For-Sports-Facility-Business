'use client';

import type { SourceType } from '@/lib/types';
import { EmailDetails } from './EmailDetails';
import { InstagramDetails } from './InstagramDetails';
import { FacebookDetails } from './FacebookDetails';
import { GoogleMapsDetails } from './GoogleMapsDetails';
import { ManualDetails } from './ManualDetails';
import { GoogleFormDetails } from './GoogleFormDetails';
import { GenericDetails } from './GenericDetails';

export interface SourceDetailsProps {
  sourceType: SourceType;
  rawData: Record<string, unknown> | null;
}

/**
 * Registry of source-specific detail renderers.
 * To add a new source:
 * 1. Create a new component file (e.g., NewSourceDetails.tsx)
 * 2. Add it to this registry
 * 3. The component will automatically be used for that source type
 */
const sourceRenderers: Record<SourceType, React.ComponentType<{ rawData: Record<string, unknown> | null }>> = {
  email: EmailDetails,
  instagram: InstagramDetails,
  facebook: FacebookDetails,
  google_maps: GoogleMapsDetails,
  manual: ManualDetails,
  google_form: GoogleFormDetails,
};

/**
 * SourceDetails - Modular component for rendering source-specific raw data
 *
 * This component uses a registry pattern to select the appropriate renderer
 * based on the source type. Each source type has its own dedicated component
 * that knows how to display its specific data structure.
 *
 * Adding a new source:
 * 1. Create a new XxxDetails.tsx component in this directory
 * 2. Add the source type to the sourceRenderers registry above
 * 3. Optionally add TypeScript types in lib/types.ts
 */
export function SourceDetails({ sourceType, rawData }: SourceDetailsProps) {
  // Get the renderer for this source type, fallback to generic if not found
  const Renderer = sourceRenderers[sourceType] || GenericDetails;

  return <Renderer rawData={rawData} />;
}

// Re-export all components for direct use if needed
export { EmailDetails } from './EmailDetails';
export { InstagramDetails } from './InstagramDetails';
export { FacebookDetails } from './FacebookDetails';
export { GoogleMapsDetails } from './GoogleMapsDetails';
export { ManualDetails } from './ManualDetails';
export { GoogleFormDetails } from './GoogleFormDetails';
export { GenericDetails } from './GenericDetails';
