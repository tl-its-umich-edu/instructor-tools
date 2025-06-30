import { createContext } from 'react';

export interface AnalyticsConsentContextType {
    analyticsConsentGiven: boolean | null;
    courseIdForEvents: number
}

export const AnalyticsConsentContext = createContext<AnalyticsConsentContextType | undefined>(undefined);
