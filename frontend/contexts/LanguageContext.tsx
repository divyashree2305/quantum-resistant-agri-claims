'use client';

/**
 * Language Context - Manages internationalization state
 * Note: Actual translations will be handled by next-intl
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Locale } from '@/types';

interface LanguageContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('en');

  // Load language preference from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedLocale = localStorage.getItem('app_locale') as Locale | null;
      if (savedLocale && (savedLocale === 'en' || savedLocale === 'es')) {
        setLocaleState(savedLocale);
      } else {
        // Detect browser language
        const browserLang = navigator.language.split('-')[0];
        setLocaleState(browserLang === 'es' ? 'es' : 'en');
      }
    }
  }, []);

  // Save language preference to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('app_locale', locale);
    }
  }, [locale]);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
  };

  return (
    <LanguageContext.Provider
      value={{
        locale,
        setLocale,
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

