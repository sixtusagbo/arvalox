'use client';

import { useState, useEffect } from 'react';
import { AuthService } from '@/lib/auth';
import { formatCurrency, getLocaleForCurrency } from '@/lib/currencies';

interface OrganizationCurrency {
  currency_code: string;
  currency_symbol: string;
  currency_name: string;
}

export function useCurrency() {
  const [currency, setCurrency] = useState<OrganizationCurrency>({
    currency_code: 'NGN',
    currency_symbol: '₦',
    currency_name: 'Nigerian Naira'
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCurrency = async () => {
      try {
        const organization = await AuthService.getOrganization();
        setCurrency({
          currency_code: organization.currency_code,
          currency_symbol: organization.currency_symbol,
          currency_name: organization.currency_name
        });
      } catch (error) {
        // Keep default NGN if error fetching organization
        console.error('Error loading organization currency:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCurrency();
  }, []);

  const formatAmount = (amount: number): string => {
    if (loading) return `${currency.currency_symbol}${amount.toLocaleString()}`;
    
    const locale = getLocaleForCurrency(currency.currency_code);
    return formatCurrency(amount, currency.currency_code, locale);
  };

  const formatAmountWithSymbol = (amount: number): string => {
    if (loading) return `${currency.currency_symbol}${amount.toLocaleString()}`;
    
    return `${currency.currency_symbol}${amount.toLocaleString()}`;
  };

  return {
    currency,
    loading,
    formatAmount,
    formatAmountWithSymbol,
  };
}