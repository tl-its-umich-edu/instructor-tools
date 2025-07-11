
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
          console.log('new event courseName', analyticsConsentContext.eventInfo.courseName);
          console.log('new event termId', analyticsConsentContext.eventInfo.termId);
          console.log('new event termName', analyticsConsentContext.eventInfo.termName);
          console.log('new event accountId', analyticsConsentContext.eventInfo.accountId);
          console.log('new event accountName', analyticsConsentContext.eventInfo.accountName);
          ReactGA.event(name, {
            ...params, 
            course_id: analyticsConsentContext.eventInfo.courseId,
            course_name: analyticsConsentContext.eventInfo.courseName,
            term_id: analyticsConsentContext.eventInfo.termId,
            term_name: analyticsConsentContext.eventInfo.termName,
            account_id: analyticsConsentContext.eventInfo.accountId,
            account_name: analyticsConsentContext.eventInfo.accountName
          });
        } catch (error) {
          console.error('Error sending Google Analytics event:', error);
        }
      }
    },
    [analyticsConsentContext]
  );

  return { sendAnalyticsEvent };
}