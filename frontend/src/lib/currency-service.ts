import { AuthService } from './auth';
import { formatCurrency, getLocaleForCurrency } from './currencies';

interface OrganizationCurrency {
  currency_code: string;
  currency_symbol: string;
  currency_name: string;
}

class CurrencyService {
  private static currency: OrganizationCurrency | null = null;
  private static initialized = false;
  private static lastFetchTime = 0;
  private static CACHE_DURATION = 30000; // 30 seconds cache

  static async initialize(): Promise<void> {
    const now = Date.now();
    
    // Use cache if recent and valid
    if (this.initialized && this.currency && (now - this.lastFetchTime) < this.CACHE_DURATION) {
      return;
    }

    try {
      const organization = await AuthService.getOrganization();
      this.currency = {
        currency_code: organization.currency_code,
        currency_symbol: organization.currency_symbol,
        currency_name: organization.currency_name
      };
      this.initialized = true;
      this.lastFetchTime = now;
    } catch (error) {
      // Fallback to NGN if organization fetch fails
      this.currency = {
        currency_code: 'NGN',
        currency_symbol: '₦',
        currency_name: 'Nigerian Naira'
      };
      this.initialized = true;
      this.lastFetchTime = now;
    }
  }

  static getCurrency(): OrganizationCurrency {
    return this.currency || {
      currency_code: 'NGN',
      currency_symbol: '₦',
      currency_name: 'Nigerian Naira'
    };
  }

  static async formatAmount(amount: number): Promise<string> {
    await this.initialize();
    const currency = this.getCurrency();
    const locale = getLocaleForCurrency(currency.currency_code);
    return formatCurrency(amount, currency.currency_code, locale);
  }

  static formatAmountSync(amount: number): string {
    const now = Date.now();
    
    // Try to refresh cache if it's stale or not initialized
    if (!this.initialized || (now - this.lastFetchTime) > this.CACHE_DURATION) {
      // For sync method, we can't await, so we trigger initialization in background
      this.initialize().catch(() => {
        // If initialization fails, continue with cached/fallback data
      });
    }
    
    const currency = this.getCurrency();
    const locale = getLocaleForCurrency(currency.currency_code);
    return formatCurrency(amount, currency.currency_code, locale);
  }

  static formatAmountWithSymbol(amount: number): string {
    const currency = this.getCurrency();
    return `${currency.currency_symbol}${amount.toLocaleString()}`;
  }

  // Reset cache when organization is updated
  static reset(): void {
    this.currency = null;
    this.initialized = false;
    this.lastFetchTime = 0;
  }
}

export { CurrencyService };