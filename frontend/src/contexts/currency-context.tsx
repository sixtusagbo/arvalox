'use client';

import { createContext, useContext, useEffect, ReactNode } from 'react';
import { CurrencyService } from '@/lib/currency-service';

interface CurrencyContextType {
  formatAmount: (amount: number) => string;
  formatAmountWithSymbol: (amount: number) => string;
}

const CurrencyContext = createContext<CurrencyContextType | undefined>(undefined);

export function CurrencyProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    // Initialize currency service on app load
    CurrencyService.initialize().catch(console.error);
  }, []);

  const contextValue: CurrencyContextType = {
    formatAmount: (amount: number) => CurrencyService.formatAmountSync(amount),
    formatAmountWithSymbol: (amount: number) => CurrencyService.formatAmountWithSymbol(amount),
  };

  return (
    <CurrencyContext.Provider value={contextValue}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrencyContext() {
  const context = useContext(CurrencyContext);
  if (context === undefined) {
    throw new Error('useCurrencyContext must be used within a CurrencyProvider');
  }
  return context;
}