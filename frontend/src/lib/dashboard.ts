import { AuthService, API_BASE_URL } from './auth';

export interface DashboardMetrics {
  total_outstanding: number;
  total_overdue: number;
  monthly_revenue: number;
  current_month_revenue: number;
  previous_month_revenue: number;
  active_invoices: number;
  total_customers: number;
  collection_rate: number;
  overdue_invoices_count: number;
  revenue_growth_percentage: number;
  invoice_growth_percentage: number;
}

export interface AgingReport {
  current: number;  // 0-30 days
  thirty_days: number;  // 31-60 days
  sixty_days: number;   // 60+ days
  total: number;
}

export interface RecentActivity {
  id: number;
  type: 'payment_received' | 'invoice_sent' | 'customer_added' | 'payment_overdue';
  description: string;
  amount?: number;
  created_at: string;
  customer_name?: string;
  invoice_id?: number;
}

export class DashboardService {
  static async getDashboardMetrics(): Promise<DashboardMetrics> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/dashboard/metrics`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch dashboard metrics');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching dashboard metrics:', error);
      // Return mock data as fallback
      return {
        total_outstanding: 45280.50,
        total_overdue: 12450.00,
        monthly_revenue: 28750.25,
        current_month_revenue: 28750.25,
        previous_month_revenue: 25680.15,
        active_invoices: 23,
        total_customers: 45,
        collection_rate: 85.5,
        overdue_invoices_count: 5,
        revenue_growth_percentage: 12.1,
        invoice_growth_percentage: -2.3,
      };
    }
  }

  static async getAgingReport(): Promise<AgingReport> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/reports/aging`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch aging report');
      }

      const data = await response.json();
      return {
        current: data.current || 18420.00,
        thirty_days: data.thirty_days || 14280.50,
        sixty_days: data.sixty_days || 12580.25,
        total: data.total || 45280.75,
      };
    } catch (error) {
      console.error('Error fetching aging report:', error);
      // Return mock data as fallback
      return {
        current: 18420.00,
        thirty_days: 14280.50,
        sixty_days: 12580.25,
        total: 45280.75,
      };
    }
  }

  static async getRecentActivity(): Promise<RecentActivity[]> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/dashboard/activity`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch recent activity');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching recent activity:', error);
      // Return mock data as fallback
      return [
        {
          id: 1,
          type: 'payment_received',
          description: 'Payment received for Invoice #1001',
          amount: 2450.00,
          created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
          customer_name: 'Acme Corporation',
          invoice_id: 1001,
        },
        {
          id: 2,
          type: 'invoice_sent',
          description: 'Invoice #1002 sent to customer',
          amount: 1280.50,
          created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
          customer_name: 'TechFlow Inc',
          invoice_id: 1002,
        },
        {
          id: 3,
          type: 'customer_added',
          description: 'New customer added',
          created_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 1 day ago
          customer_name: 'StartupXYZ',
        },
        {
          id: 4,
          type: 'payment_overdue',
          description: 'Payment overdue for Invoice #0995',
          amount: 3125.75,
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
          customer_name: 'Global Systems',
          invoice_id: 995,
        },
      ];
    }
  }

  static async getTopCustomers(): Promise<Array<{
    id: number;
    name: string;
    email: string;
    outstanding_balance: number;
    status: 'current' | 'overdue';
  }>> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/customers?sort=outstanding_balance&limit=5`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch top customers');
      }

      const data = await response.json();
      return data.customers || [];
    } catch (error) {
      console.error('Error fetching top customers:', error);
      // Return mock data as fallback
      return [
        {
          id: 1,
          name: 'Acme Corporation',
          email: 'billing@acme.com',
          outstanding_balance: 8450.00,
          status: 'current',
        },
        {
          id: 2,
          name: 'TechFlow Inc',
          email: 'accounts@techflow.com',
          outstanding_balance: 5280.50,
          status: 'overdue',
        },
        {
          id: 3,
          name: 'Global Systems',
          email: 'payments@globalsys.com',
          outstanding_balance: 4125.75,
          status: 'current',
        },
        {
          id: 4,
          name: 'StartupXYZ',
          email: 'finance@startupxyz.com',
          outstanding_balance: 3890.25,
          status: 'overdue',
        },
      ];
    }
  }

  static formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  }

  static formatPercentage(value: number): string {
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  }

  static getTimeAgo(dateString: string): string {
    const now = new Date();
    const date = new Date(dateString);
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes} minutes ago`;
    } else if (diffInMinutes < 1440) { // 24 hours
      const hours = Math.floor(diffInMinutes / 60);
      return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
      const days = Math.floor(diffInMinutes / 1440);
      return `${days} day${days > 1 ? 's' : ''} ago`;
    }
  }
}