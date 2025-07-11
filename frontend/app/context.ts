import { createContext } from 'react';

export interface AnalyticsConsentContextType {
    analyticsConsentGiven: boolean | null;
    eventInfo: {
        courseId: number;
        courseName: string | null;
        termId: number | null;
        termName: string | null;
        accountId: number | null;
        accountName: string | null;
    }
}

export const AnalyticsConsentContext = createContext<AnalyticsConsentContextType | undefined>(undefined);
