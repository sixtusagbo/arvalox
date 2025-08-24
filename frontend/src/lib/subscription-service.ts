import { API_BASE_URL, AuthService } from './auth';

export interface SubscriptionPlan {
  id: number;
  name: string;
  plan_type: 'free' | 'starter' | 'professional' | 'enterprise';
  description: string | null;
  monthly_price: number;
  yearly_price: number;
  currency: string;
  max_invoices_per_month: number | null;
  max_customers: number | null;
  max_team_members: number | null;
  custom_branding: boolean;
  api_access: boolean;
  advanced_reporting: boolean;
  priority_support: boolean;
  multi_currency: boolean;
  is_active: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface Subscription {
  id: number;
  organization_id: number;
  plan_id: number;
  status: 'active' | 'inactive' | 'canceled' | 'past_due' | 'trialing' | 'paused';
  billing_interval: 'monthly' | 'yearly';
  started_at: string;
  current_period_start: string;
  current_period_end: string;
  trial_start: string | null;
  trial_end: string | null;
  canceled_at: string | null;
  ended_at: string | null;
  paystack_customer_code: string | null;
  paystack_subscription_code: string | null;
  next_payment_date: string | null;
  current_invoice_count: number;
  current_customer_count: number;
  current_team_member_count: number;
  is_active: boolean;
  is_trialing: boolean;
  days_until_expiry: number | null;
  plan: SubscriptionPlan;
  created_at: string;
  updated_at: string;
}

export interface UsageStats {
  current_invoice_count: number;
  current_customer_count: number;
  current_team_member_count: number;
  max_invoices_per_month: number | null;
  max_customers: number | null;
  max_team_members: number | null;
  invoice_usage_percentage: number | null;
  customer_usage_percentage: number | null;
  team_member_usage_percentage: number | null;
  can_create_invoice: boolean;
  can_add_customer: boolean;
  can_add_team_member: boolean;
}

export interface UsageRecord {
  id: number;
  subscription_id: number;
  month: number;
  year: number;
  invoices_created: number;
  customers_created: number;
  team_members_added: number;
  api_calls_made: number;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionSummary {
  subscription: Subscription;
  usage_stats: UsageStats;
  recent_usage: UsageRecord[];
}

export interface PlanComparison {
  current_plan: SubscriptionPlan;
  available_plans: SubscriptionPlan[];
  upgrade_options: SubscriptionPlan[];
  downgrade_options: SubscriptionPlan[];
}

export interface CreateSubscriptionRequest {
  plan_id: number;
  billing_interval: 'monthly' | 'yearly';
  start_trial: boolean;
  trial_days: number;
}

export interface UpdateSubscriptionRequest {
  plan_id?: number;
  billing_interval?: 'monthly' | 'yearly';
  paystack_customer_code?: string;
  paystack_subscription_code?: string;
}

export interface CancelSubscriptionRequest {
  cancel_immediately: boolean;
  reason?: string;
}

export interface TrialExtensionRequest {
  additional_days: number;
  reason?: string;
}

export class SubscriptionService {
  static async getPlans(): Promise<SubscriptionPlan[]> {
    const response = await fetch(`${API_BASE_URL}/subscriptions/plans`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch subscription plans');
    }
    
    return await response.json();
  }

  static async getPlan(planId: number): Promise<SubscriptionPlan> {
    const response = await fetch(`${API_BASE_URL}/subscriptions/plans/${planId}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch subscription plan');
    }
    
    return await response.json();
  }

  static async getCurrentSubscription(): Promise<SubscriptionSummary> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/current`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch current subscription');
    }
    
    return await response.json();
  }

  static async createSubscription(request: CreateSubscriptionRequest): Promise<Subscription> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create subscription');
    }
    
    return await response.json();
  }

  static async upgradeSubscription(request: UpdateSubscriptionRequest): Promise<Subscription> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/upgrade`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to upgrade subscription');
    }
    
    return await response.json();
  }

  static async cancelSubscription(request: CancelSubscriptionRequest): Promise<Subscription> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/cancel`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to cancel subscription');
    }
    
    return await response.json();
  }

  static async reactivateSubscription(): Promise<Subscription> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/reactivate`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to reactivate subscription');
    }
    
    return await response.json();
  }

  static async getUsageStats(): Promise<UsageStats> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/usage`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch usage statistics');
    }
    
    return await response.json();
  }

  static async getUsageHistory(limit: number = 12): Promise<UsageRecord[]> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/usage/history?limit=${limit}`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch usage history');
    }
    
    return await response.json();
  }

  static async comparePlans(): Promise<PlanComparison> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/compare`);
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to compare plans');
    }
    
    return await response.json();
  }

  static async extendTrial(request: TrialExtensionRequest): Promise<Subscription> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/extend-trial`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to extend trial');
    }
    
    return await response.json();
  }

  static formatPrice(amount: number, currency: string = 'NGN'): string {
    if (amount === 0) return 'Free';
    
    // Subscription plans should always use NGN because we use Paystack for payments
    // Use the passed currency parameter (which should be NGN for subscription plans)
    const symbol = currency === 'NGN' ? '₦' : 
                   currency === 'GBP' ? '£' :
                   currency === 'EUR' ? '€' :
                   currency === 'USD' ? '$' : 
                   '$';
    
    // Use explicit locale formatting for consistent results
    const formattedAmount = new Intl.NumberFormat('en-NG', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
      useGrouping: true
    }).format(amount);
    
    return `${symbol}${formattedAmount}`;
  }

  static getPlanColor(planType: string): string {
    switch (planType) {
      case 'free':
        return 'text-gray-600 bg-gray-50 border-gray-200';
      case 'starter':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'professional':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'enterprise':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  }

  static getUsageColor(percentage: number | null): string {
    if (percentage === null) return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20';
    if (percentage >= 90) return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20';
    if (percentage >= 75) return 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20';
    return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-900/20';
  }

  static formatUsagePercentage(percentage: number | null, unlimited: boolean = false): string {
    if (unlimited) return 'Unlimited';
    if (percentage === null) return 'N/A';
    return `${Math.round(percentage)}%`;
  }

  // Paystack integration methods
  static async initializePayment(
    planId: number, 
    billingInterval: 'monthly' | 'yearly',
    callbackUrl: string
  ): Promise<{ authorization_url: string; access_code: string; reference: string }> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/initialize-payment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        plan_id: planId,
        billing_interval: billingInterval,
        callback_url: callbackUrl
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to initialize payment');
    }
    
    const result = await response.json();
    return result.data;
  }

  static async verifyPayment(
    reference: string,
    planId: number,
    billingInterval: 'monthly' | 'yearly'
  ): Promise<Subscription> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/subscriptions/verify-payment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        reference,
        plan_id: planId,
        billing_interval: billingInterval
      }),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to verify payment');
    }
    
    return await response.json();
  }

  static redirectToPaystack(authorizationUrl: string): void {
    window.location.href = authorizationUrl;
  }
}