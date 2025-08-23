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

  static async initialize(): Promise<void> {
    if (this.initialized && this.currency) return;

    try {
      const organization = await AuthService.getOrganization();
      this.currency = {
        currency_code: organization.currency_code,
        currency_symbol: organization.currency_symbol,
        currency_name: organization.currency_name
      };
      this.initialized = true;
    } catch (error) {
      // Fallback to NGN if organization fetch fails
      this.currency = {
        currency_code: 'NGN',
        currency_symbol: '₦',
        currency_name: 'Nigerian Naira'
      };
      this.initialized = true;
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
  }
}

export { CurrencyService };