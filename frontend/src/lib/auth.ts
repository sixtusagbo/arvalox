export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
  organization_name: string;
}

export const API_BASE_URL = "http://localhost:8000/api/v1";

export class AuthService {
  static getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  static getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("refresh_token");
  }

  static setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
  }

  static clearTokens(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  static async refreshToken(): Promise<{ access_token: string; refresh_token: string } | null> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) {
        this.clearTokens();
        return null;
      }

      const data = await response.json();
      this.setTokens(data.access_token, data.refresh_token);
      return data;
    } catch (error) {
      this.clearTokens();
      return null;
    }
  }

  static async fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
    let token = this.getToken();
    
    if (!token) {
      throw new Error("No access token available");
    }

    // First attempt with current token
    let response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        "Authorization": `Bearer ${token}`,
      },
    });

    // If unauthorized, try to refresh token
    if (response.status === 401) {
      const newTokens = await this.refreshToken();
      if (newTokens) {
        response = await fetch(url, {
          ...options,
          headers: {
            ...options.headers,
            "Authorization": `Bearer ${newTokens.access_token}`,
          },
        });
      }
    }

    return response;
  }

  static async getCurrentUser(): Promise<User | null> {
    try {
      const response = await this.fetchWithAuth(`${API_BASE_URL}/auth/me`);
      
      if (!response.ok) {
        this.clearTokens();
        return null;
      }

      return await response.json();
    } catch (error) {
      this.clearTokens();
      return null;
    }
  }

  static async login(email: string, password: string): Promise<{ access_token: string; refresh_token: string }> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Login failed");
    }

    const data = await response.json();
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  static async register(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    organization_name: string;
    organization_slug?: string;
  }): Promise<{ access_token: string; refresh_token: string }> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Registration failed");
    }

    const data = await response.json();
    this.setTokens(data.access_token, data.refresh_token);
    return data;
  }

  static async requestPasswordReset(email: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/auth/password-reset/request`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to send reset email");
    }

    return await response.json();
  }

  static async confirmPasswordReset(token: string, newPassword: string): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/auth/password-reset/confirm`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ 
        token, 
        new_password: newPassword 
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to reset password");
    }

    return await response.json();
  }

  static logout(): void {
    this.clearTokens();
  }

  static async updateProfile(profileData: {
    first_name?: string;
    last_name?: string;
    email?: string;
  }): Promise<User> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/auth/me/profile`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(profileData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to update profile");
    }

    return await response.json();
  }

  static async changePassword(passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<{ message: string }> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/auth/me/password`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(passwordData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to change password");
    }

    return await response.json();
  }

  static async getOrganization(): Promise<{
    id: number;
    name: string;
    slug: string;
    created_at: string;
    updated_at: string;
  }> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/auth/me/organization`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to get organization info");
    }

    return await response.json();
  }

  static async updateOrganization(orgData: {
    name?: string;
    slug?: string;
  }): Promise<{
    id: number;
    name: string;
    slug: string;
    created_at: string;
    updated_at: string;
  }> {
    const response = await this.fetchWithAuth(`${API_BASE_URL}/auth/me/organization`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(orgData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to update organization");
    }

    return await response.json();
  }
}