import { AuthService, API_BASE_URL } from './auth';

export interface DashboardOverview {
  report_date: string;
  date_range: {
    from: string;
    to: string;
  };
  revenue_metrics: {
    total_revenue: number;
    outstanding_amount: number;
    invoice_count: number;
    revenue_growth_percentage: number;
  };
  aging_metrics: {
    total_overdue: number;
    overdue_percentage: number;
    collection_efficiency: number;
    average_days_outstanding: number;
  };
  customer_metrics: {
    total_customers: number;
    new_customers: number;
    active_customers: number;
  };
  invoice_metrics: {
    total_count: number;
    overdue_count: number;
    draft_count: number;
    sent_count: number;
    paid_count: number;
  };
  payment_metrics: {
    payment_count: number;
    total_payments: number;
    average_payment_amount: number;
  };
  recent_activity: RecentActivity[];
  top_customers: TopCustomer[];
}

export interface QuickStats {
  total_revenue_this_month: number;
  total_outstanding: number;
  overdue_amount: number;
  total_customers: number;
  invoices_this_month: number;
  payments_this_month: number;
}

export interface KPISummary {
  total_revenue: number;
  outstanding_amount: number;
  overdue_amount: number;
  collection_efficiency: number;
  revenue_growth: number;
  total_customers: number;
  active_invoices: number;
  overdue_invoices: number;
}

export interface RecentActivity {
  id: number;
  type: 'invoice' | 'payment';
  description: string;
  amount: number;
  customer_name: string;
  date: string;
  status: string;
}

export interface TopCustomer {
  customer_id: number;
  customer_name: string;
  total_revenue: number;
  outstanding_amount: number;
  invoice_count: number;
  payment_count: number;
}

export interface AgingReport {
  report_date: string;
  organization_id: number;
  summary: AgingSummary;
  customer_summaries: CustomerAgingSummary[];
  invoice_details: AgingInvoiceDetail[];
}

export interface AgingSummary {
  current: { count: number; amount: number };
  days_1_30: { count: number; amount: number };
  days_31_60: { count: number; amount: number };
  days_61_90: { count: number; amount: number };
  days_over_90: { count: number; amount: number };
  total: { count: number; amount: number };
}

export interface CustomerAgingSummary {
  customer_id: number;
  customer_name: string;
  customer_code: string;
  total: number;
  current: number;
  days_1_30: number;
  days_31_60: number;
  days_61_90: number;
  days_over_90: number;
}

export interface AgingInvoiceDetail {
  invoice_id: number;
  invoice_number: string;
  customer_name: string;
  invoice_date: string;
  due_date: string;
  total_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  days_overdue: number;
  aging_bucket: string;
}

export interface AgingMetrics {
  total_outstanding: number;
  total_overdue: number;
  overdue_percentage: number;
  average_days_outstanding: number;
  worst_aging_customer: string | null;
  worst_aging_amount: number;
  collection_efficiency: number;
}

export interface AgingAlerts {
  critical_overdue_count: number;
  critical_overdue_amount: number;
  new_overdue_count: number;
  new_overdue_amount: number;
  collection_risk_customers: string[];
  total_at_risk_amount: number;
}

export class ReportsService {
  static async getDashboardOverview(dateFrom?: string, dateTo?: string): Promise<DashboardOverview> {
    const queryParams = new URLSearchParams();
    if (dateFrom) queryParams.append('date_from', dateFrom);
    if (dateTo) queryParams.append('date_to', dateTo);

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/dashboard?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch dashboard overview');
    }

    return await response.json();
  }

  static async getQuickStats(): Promise<QuickStats> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/reports/dashboard/quick-stats`);

    if (!response.ok) {
      throw new Error('Failed to fetch quick stats');
    }

    return await response.json();
  }

  static async getKPISummary(dateFrom?: string, dateTo?: string): Promise<KPISummary> {
    const queryParams = new URLSearchParams();
    if (dateFrom) queryParams.append('date_from', dateFrom);
    if (dateTo) queryParams.append('date_to', dateTo);

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/dashboard/kpis?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch KPI summary');
    }

    return await response.json();
  }

  static async getAgingReport(asOfDate?: string, customerId?: number, includePaid?: boolean): Promise<AgingReport> {
    const queryParams = new URLSearchParams();
    if (asOfDate) queryParams.append('as_of_date', asOfDate);
    if (customerId) queryParams.append('customer_id', customerId.toString());
    if (includePaid !== undefined) queryParams.append('include_paid', includePaid.toString());

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/aging?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch aging report');
    }

    return await response.json();
  }

  static async getAgingMetrics(asOfDate?: string): Promise<{ metrics: AgingMetrics; aging_summary: AgingSummary }> {
    const queryParams = new URLSearchParams();
    if (asOfDate) queryParams.append('as_of_date', asOfDate);

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/aging/metrics?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch aging metrics');
    }

    return await response.json();
  }

  static async getAgingAlerts(): Promise<{ alerts: AgingAlerts }> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/reports/aging/alerts`);

    if (!response.ok) {
      throw new Error('Failed to fetch aging alerts');
    }

    return await response.json();
  }

  static async getTopCustomers(limit: number = 10): Promise<TopCustomer[]> {
    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/dashboard/top-customers?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch top customers');
    }

    return await response.json();
  }

  static async getRecentActivity(limit: number = 20): Promise<RecentActivity[]> {
    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/dashboard/recent-activity?limit=${limit}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch recent activity');
    }

    return await response.json();
  }

  static async exportAgingReport(format: 'csv' | 'pdf' = 'csv', options: {
    customerId?: number;
    includePaid?: boolean;
    asOfDate?: string;
  } = {}): Promise<Blob> {
    const queryParams = new URLSearchParams();
    queryParams.append('format', format);
    if (options.customerId) queryParams.append('customer_id', options.customerId.toString());
    if (options.includePaid !== undefined) queryParams.append('include_paid', options.includePaid.toString());
    if (options.asOfDate) queryParams.append('as_of_date', options.asOfDate);

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/export/aging-report?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to export aging report');
    }

    return await response.blob();
  }

  static formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  }

  static formatPercentage(value: number): string {
    return `${value.toFixed(1)}%`;
  }

  static formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  static getAgingBucketColor(bucket: string): string {
    switch (bucket) {
      case 'current':
        return 'text-green-600';
      case 'days_1_30':
        return 'text-yellow-600';
      case 'days_31_60':
        return 'text-orange-600';
      case 'days_61_90':
        return 'text-red-600';
      case 'days_over_90':
        return 'text-red-800';
      default:
        return 'text-gray-600';
    }
  }

  static getAgingBucketLabel(bucket: string): string {
    switch (bucket) {
      case 'current':
        return 'Current';
      case 'days_1_30':
        return '1-30 Days';
      case 'days_31_60':
        return '31-60 Days';
      case 'days_61_90':
        return '61-90 Days';
      case 'days_over_90':
        return '90+ Days';
      default:
        return bucket;
    }
  }

  static calculateGrowthPercentage(current: number, previous: number): number {
    if (previous === 0) return current > 0 ? 100 : 0;
    return ((current - previous) / previous) * 100;
  }

  static getGrowthColor(percentage: number): string {
    if (percentage > 0) return 'text-green-600';
    if (percentage < 0) return 'text-red-600';
    return 'text-gray-600';
  }

  static getGrowthIcon(percentage: number): string {
    if (percentage > 0) return '↑';
    if (percentage < 0) return '↓';
    return '→';
  }

  // Alert-related methods
  static async getOverdueInvoices(daysOverdue: number = 1, customerId?: number): Promise<AgingInvoiceDetail[]> {
    const queryParams = new URLSearchParams();
    queryParams.append('days_overdue', daysOverdue.toString());
    if (customerId) queryParams.append('customer_id', customerId.toString());

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/reports/aging/overdue?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch overdue invoices');
    }

    return await response.json();
  }

  static async sendInvoiceReminder(invoiceId: number): Promise<{ message: string; email_sent: boolean; status_updated: boolean }> {
    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/invoices/${invoiceId}/send`,
      {
        method: 'POST',
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to send invoice reminder');
    }

    return await response.json();
  }

  static async sendBulkReminders(invoiceIds: number[]): Promise<{ 
    successful: number; 
    failed: number; 
    details: Array<{ invoiceId: number; success: boolean; message?: string }> 
  }> {
    const results = await Promise.allSettled(
      invoiceIds.map(async (invoiceId) => {
        try {
          const result = await this.sendInvoiceReminder(invoiceId);
          return { invoiceId, success: true, message: result.message };
        } catch (error) {
          return { 
            invoiceId, 
            success: false, 
            message: error instanceof Error ? error.message : 'Failed to send reminder'
          };
        }
      })
    );

    const details = results.map(result => 
      result.status === 'fulfilled' ? result.value : result.reason
    );

    const successful = details.filter(d => d.success).length;
    const failed = details.filter(d => !d.success).length;

    return { successful, failed, details };
  }
}