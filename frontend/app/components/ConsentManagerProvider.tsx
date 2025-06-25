import React, { useCallback, useEffect, useState } from 'react';
import { AnalyticsConsentContext, AnalyticsConsentContextType } from '../context';


// Define the structure of the window.umConsentManager object
interface ConsentChangeEvent {
  cookie : {
    categories: string[];
  }
}
interface UmConsentCustomManager {
  enabled: boolean;
  alwaysShow: boolean;
  rootDomain: string | false;
  preferencePanel: {
    beforeCategories: boolean; // HTML
    afterCategories: boolean; // HTML
  };
}
interface UmConsentManagerConfig {
  //callback function to handle consent changes
  onConsentChange: (event: ConsentChangeEvent) => void;
  // other UmConsentManager required properties
  mode: string; // values: 'prod', 'dev'
  customManager: UmConsentCustomManager;
  googleAnalyticsCustom: {
    streamConfig: {
      cookie_flags: string; // e.g., 'SameSite=None; Secure'
    };
  }
  privacyUrl: string | false;
  googleAnalyticsID: string | false;
  cookies: {
    necessary: Array<{ name: string; domain: string; regex: string }>;
    analytics: Array<{ name: string; domain: string; regex: string }>;
  };
}

declare global {
  interface Window {
    umConsentManager: UmConsentManagerConfig;
  }
}

interface ConsentManagerProviderProps {
  children: React.ReactNode;
  consentManagerScriptUrl: string;
  googleAnalyticsID: string;
  // Optional properties for the consent manager configuration
  alwaysShow?: boolean;
  rootDomain?: string; // e.g., 'ngrok-free.app' for local testing
  mode?: 'prod' | 'dev';
  privacyUrl?: string | false;
}

export function ConsentManagerProvider({
  children,
  consentManagerScriptUrl,
  googleAnalyticsID,
  alwaysShow = false,
  rootDomain = '',
  mode = 'prod',
  privacyUrl = false
}: ConsentManagerProviderProps) {
  const [analyticsConsentGiven, setAnalyticsConsentGiven] = useState<boolean | null>(null);

  const handleConsentChange = useCallback(({cookie}: ConsentChangeEvent) => {
    if (cookie && cookie.categories.includes('analytics')) {
      setAnalyticsConsentGiven(true);
    } else {
      setAnalyticsConsentGiven(false);
    }
  }, []);

  
  useEffect(() => {
    // Guard against Server-Side Rendering (SSR) environments
    if (typeof window === 'undefined') {
      return;
    }
    // todo: verify settings exist
    if (!consentManagerScriptUrl || !googleAnalyticsID) {
      !googleAnalyticsID && console.warn('Google Analytics ID is not provided, analytics tracking not initialized.');
      !consentManagerScriptUrl && console.warn('Consent manager script URL is not provided, analytics tracking not initialized.');
      return;
    }
    
    // 1. Set window.umConsentManager *before* injecting the script
    const enabledCustomManager = alwaysShow !== false || rootDomain !== '';
    const consentConfig: UmConsentManagerConfig = {
      onConsentChange: handleConsentChange,
      mode: mode, // default is 'prod'
      customManager: {
        enabled: enabledCustomManager,
        alwaysShow: alwaysShow,
        rootDomain: enabledCustomManager ? rootDomain : false,
        preferencePanel: {
          beforeCategories: false, // HTML
          afterCategories: false // HTML
        }
      },
      googleAnalyticsCustom: {
        streamConfig: { cookie_flags: 'SameSite=None; Secure' }
      },
      privacyUrl: privacyUrl,
      googleAnalyticsID: googleAnalyticsID,
      cookies: {
        necessary: [],
        analytics: [],
      }
    };
    window.umConsentManager = consentConfig;

    // 2. Create & inject the script
    const script = document.createElement('script');
    script.src = consentManagerScriptUrl;
    script.async = true; // or script.defer = true
    script.id = 'um-consent-manager-script'; // Good for identification and cleanup
    
    script.onerror = (error: Event | string) => {
      console.error('Failed to load consent manager script:', error);
    };
    document.head.appendChild(script);

    // 3. Cleanup function to remove the script when the component unmounts
    return () => {
      console.log('Cleaning up ConsentManagerProvider');
      const existingScript = document.getElementById('um-consent-manager-script');
      if (existingScript && existingScript.parentNode) {
        existingScript.parentNode.removeChild(existingScript);
      }
    };

  }, [handleConsentChange, googleAnalyticsID, alwaysShow, consentManagerScriptUrl, mode, privacyUrl]);

  const contextValue: AnalyticsConsentContextType = {
    analyticsConsentGiven: analyticsConsentGiven
  };
  
  return (
    <AnalyticsConsentContext.Provider value={contextValue}>
      {children}
    </AnalyticsConsentContext.Provider>
  );
}