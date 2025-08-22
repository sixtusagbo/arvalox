import { AuthService, API_BASE_URL } from './auth';

export interface Payment {
  id: number;
  organization_id: number;
  invoice_id: number;
  user_id: number;
  payment_date: string;
  amount: number;
  payment_method: 'cash' | 'check' | 'bank_transfer' | 'credit_card' | 'online' | 'other';
  reference_number?: string;
  status: 'completed' | 'pending' | 'failed' | 'cancelled';
  notes?: string;
  invoice?: {
    id: number;
    invoice_number: string;
    customer_name?: string;
    total_amount: number;
  };
  created_at: string;
  updated_at: string;
}

export interface PaymentCreate {
  invoice_id: number;
  payment_date: string;
  amount: number;
  payment_method: 'cash' | 'check' | 'bank_transfer' | 'credit_card' | 'online' | 'other';
  reference_number?: string;
  notes?: string;
}

export interface PaymentUpdate {
  payment_date?: string;
  amount?: number;
  payment_method?: 'cash' | 'check' | 'bank_transfer' | 'credit_card' | 'online' | 'other';
  reference_number?: string;
  status?: 'completed' | 'pending' | 'failed' | 'cancelled';
  notes?: string;
}

export interface PaymentSearchParams {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  payment_method?: string;
  invoice_id?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface PaymentListResponse {
  payments: Payment[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export class PaymentService {
  static async getPayments(params: PaymentSearchParams = {}): Promise<PaymentListResponse> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/payments/?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch payments');
    }

    return await response.json();
  }

  static async getPayment(id: number): Promise<Payment> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/payments/${id}`);

    if (!response.ok) {
      throw new Error('Failed to fetch payment');
    }

    return await response.json();
  }

  static async createPayment(paymentData: PaymentCreate): Promise<Payment> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/payments/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(paymentData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create payment');
    }

    return await response.json();
  }

  static async updatePayment(id: number, paymentData: PaymentUpdate): Promise<Payment> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/payments/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(paymentData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update payment');
    }

    return await response.json();
  }

  static async deletePayment(id: number): Promise<void> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/payments/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete payment');
    }
  }

  static formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  }

  static formatPaymentMethod(method: string): string {
    switch (method) {
      case 'cash':
        return 'Cash';
      case 'check':
        return 'Check';
      case 'bank_transfer':
        return 'Bank Transfer';
      case 'credit_card':
        return 'Credit Card';
      case 'online':
        return 'Online Payment';
      case 'other':
        return 'Other';
      default:
        return method;
    }
  }

  static formatPaymentStatus(status: string): string {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'pending':
        return 'Pending';
      case 'failed':
        return 'Failed';
      case 'cancelled':
        return 'Cancelled';
      default:
        return status;
    }
  }

  static formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  static getStatusColor(status: Payment['status']): string {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }
}