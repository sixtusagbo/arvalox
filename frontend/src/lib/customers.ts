import { AuthService, API_BASE_URL } from './auth';

export interface Customer {
  id: number;
  organization_id: number;
  customer_code: string;
  name?: string;
  email?: string;
  phone?: string;
  billing_address?: string;
  shipping_address?: string;
  credit_limit: number;
  payment_terms: number;
  tax_id?: string;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  updated_at: string;
}

export interface CustomerCreate {
  customer_code: string;
  name?: string;
  email?: string;
  phone?: string;
  billing_address?: string;
  shipping_address?: string;
  credit_limit?: number;
  payment_terms?: number;
  tax_id?: string;
  status?: 'active' | 'inactive' | 'suspended';
}

export interface CustomerUpdate {
  customer_code?: string;
  name?: string;
  email?: string;
  phone?: string;
  billing_address?: string;
  shipping_address?: string;
  credit_limit?: number;
  payment_terms?: number;
  tax_id?: string;
  status?: 'active' | 'inactive' | 'suspended';
}

export interface CustomerListResponse {
  customers: Customer[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface CustomerSearchParams {
  search?: string;
  status?: 'active' | 'inactive' | 'suspended';
  payment_terms_min?: number;
  payment_terms_max?: number;
  has_credit_limit?: boolean;
  page?: number;
  per_page?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export class CustomerService {
  static async getCustomers(params: CustomerSearchParams = {}): Promise<CustomerListResponse> {
    try {
      const queryParams = new URLSearchParams();
      
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });

      const response = await AuthService.fetchWithAuth(
        `${API_BASE_URL}/customers/?${queryParams.toString()}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch customers');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching customers:', error);
      throw error;
    }
  }

  static async getCustomer(id: number): Promise<Customer> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/customers/${id}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch customer');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching customer:', error);
      throw error;
    }
  }

  static async createCustomer(customerData: CustomerCreate): Promise<Customer> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/customers/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(customerData),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create customer');
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating customer:', error);
      throw error;
    }
  }

  static async updateCustomer(id: number, customerData: CustomerUpdate): Promise<Customer> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/customers/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(customerData),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update customer');
      }

      return await response.json();
    } catch (error) {
      console.error('Error updating customer:', error);
      throw error;
    }
  }

  static async deleteCustomer(id: number): Promise<void> {
    try {
      const response = await AuthService.fetchWithAuth(`${API_BASE_URL}/customers/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete customer');
      }
    } catch (error) {
      console.error('Error deleting customer:', error);
      throw error;
    }
  }

  static formatStatus(status: string): string {
    switch (status) {
      case 'active':
        return 'Active';
      case 'inactive':
        return 'Inactive';
      case 'suspended':
        return 'Suspended';
      default:
        return status;
    }
  }

  static getStatusColor(status: string): string {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-50';
      case 'inactive':
        return 'text-gray-600 bg-gray-50';
      case 'suspended':
        return 'text-red-600 bg-red-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  }

  static formatCurrency(amount: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  }
}