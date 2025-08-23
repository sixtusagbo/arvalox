import { AuthService, API_BASE_URL } from './auth';

export interface InvoiceItem {
  id?: number;
  invoice_id?: number;
  description: string;
  quantity: number;
  unit_price: number;
  line_total: number;
  total_amount?: number; // For frontend compatibility
  created_at?: string;
  updated_at?: string;
}

export interface Invoice {
  id: number;
  organization_id: number;
  customer_id: number;
  user_id: number;
  invoice_number: string;
  invoice_date: string;
  due_date: string;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  paid_amount: number;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  notes?: string;
  items: InvoiceItem[];
  customer?: {
    id: number;
    name: string;
    email?: string;
    customer_code: string;
  };
  created_at: string;
  updated_at: string;
}

export interface InvoiceCreate {
  invoice_number: string;
  customer_id: number;
  invoice_date: string;
  due_date: string;
  status?: 'draft' | 'sent';
  notes?: string;
  items: Omit<InvoiceItem, 'id'>[];
}

export interface InvoiceUpdate {
  invoice_number?: string;
  customer_id?: number;
  invoice_date?: string;
  due_date?: string;
  status?: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  notes?: string;
  items?: Omit<InvoiceItem, 'id'>[];
}

export interface InvoiceSearchParams {
  page?: number;
  per_page?: number;
  search?: string;
  status?: string;
  customer_id?: number;
  date_from?: string;
  date_to?: string;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface InvoiceListResponse {
  invoices: Invoice[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export class InvoiceService {
  static async getInvoices(params: InvoiceSearchParams = {}): Promise<InvoiceListResponse> {
    const queryParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value.toString());
      }
    });

    const response = await AuthService.fetchWithAuth(
      `${API_BASE_URL}/invoices/?${queryParams.toString()}`
    );

    if (!response.ok) {
      throw new Error('Failed to fetch invoices');
    }

    return await response.json();
  }

  static async getInvoice(id: number): Promise<Invoice> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/invoices/${id}`);

    if (!response.ok) {
      throw new Error('Failed to fetch invoice');
    }

    return await response.json();
  }

  static async generateInvoiceNumber(): Promise<string> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/invoices/generate-number`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to generate invoice number');
    }

    const data = await response.json();
    return data.invoice_number;
  }

  static async createInvoice(invoiceData: InvoiceCreate): Promise<Invoice> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/invoices/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(invoiceData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to create invoice');
    }

    return await response.json();
  }

  static async updateInvoice(id: number, invoiceData: InvoiceUpdate): Promise<Invoice> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/invoices/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(invoiceData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to update invoice');
    }

    return await response.json();
  }

  static async deleteInvoice(id: number): Promise<void> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/invoices/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to delete invoice');
    }
  }

  static async downloadInvoicePDF(id: number): Promise<Blob> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/invoices/${id}/pdf`);

    if (!response.ok) {
      throw new Error('Failed to download invoice PDF');
    }

    return await response.blob();
  }

  static async sendInvoiceEmail(id: number): Promise<{message: string; email_sent: boolean; status_updated: boolean}> {
    const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/invoices/${id}/send`, {
      method: 'POST',
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to send invoice email');
    }

    return await response.json();
  }

  static formatCurrency(amount: number): string {
    // Import dynamically to avoid circular dependency
    const { CurrencyService } = require('./currency-service');
    return CurrencyService.formatAmountSync(amount);
  }

  static formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  static getStatusColor(status: Invoice['status']): string {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'sent':
        return 'bg-blue-100 text-blue-800';
      case 'paid':
        return 'bg-green-100 text-green-800';
      case 'overdue':
        return 'bg-red-100 text-red-800';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  }

  static formatStatus(status: Invoice['status']): string {
    switch (status) {
      case 'draft':
        return 'Draft';
      case 'sent':
        return 'Sent';
      case 'paid':
        return 'Paid';
      case 'overdue':
        return 'Overdue';
      case 'cancelled':
        return 'Cancelled';
      default:
        return status;
    }
  }

  static calculateDaysOverdue(dueDate: string): number {
    const due = new Date(dueDate);
    const today = new Date();
    const diffTime = today.getTime() - due.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  }

  static calculateItemTotal(quantity: number, unitPrice: number): number {
    return quantity * unitPrice;
  }

  static calculateSubtotal(items: InvoiceItem[]): number {
    if (!items || items.length === 0) return 0;
    
    return items.reduce((sum, item) => {
      // Handle both total_amount and line_total fields, with fallback calculation
      const quantity = Number(item.quantity) || 0;
      const unitPrice = Number(item.unit_price) || 0;
      const totalAmount = Number(item.total_amount) || 0;
      const lineTotal = Number(item.line_total) || 0;
      
      const itemTotal = totalAmount || lineTotal || (quantity * unitPrice) || 0;
      const validItemTotal = isNaN(itemTotal) ? 0 : itemTotal;
      const validSum = isNaN(sum) ? 0 : sum;
      
      return validSum + validItemTotal;
    }, 0);
  }

  static calculateTax(subtotal: number, taxRate: number = 0): number {
    const validSubtotal = isNaN(subtotal) ? 0 : subtotal;
    const validTaxRate = isNaN(taxRate) ? 0 : taxRate;
    return validSubtotal * (validTaxRate / 100);
  }

  static calculateTotal(subtotal: number, taxAmount: number): number {
    const validSubtotal = isNaN(subtotal) ? 0 : subtotal;
    const validTaxAmount = isNaN(taxAmount) ? 0 : taxAmount;
    return validSubtotal + validTaxAmount;
  }
}