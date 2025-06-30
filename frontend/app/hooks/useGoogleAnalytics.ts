
import ReactGA from 'react-ga4';
import { useCallback } from 'react';
import { AnalyticsConsentContextType } from '../context.js';



export function useGoogleAnalytics<Params extends object>(
  analyticsConsentContext: AnalyticsConsentContextType | undefined
) {
  const sendAnalyticsEvent = useCallback(
    (name: string, params: Params) => {
      if (analyticsConsentContext === undefined) {
        console.warn('Analytics consent context is undefined, event not sent:', name);
        return;
      }
      
      if (analyticsConsentContext.analyticsConsentGiven) {
        try {
          ReactGA.event(name, {...params, course_id: analyticsConsentContext.courseIdForEvents });
        } catch (error) {
          console.error('Error sending Google Analytics event:', error);
        }
      }
    },
    [analyticsConsentContext]
  );

  return { sendAnalyticsEvent };
}