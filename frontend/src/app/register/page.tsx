"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { CurrencyPicker } from "@/components/ui/currency-picker";
import type { Currency } from "@/lib/currencies";
import { LightModeOnly } from "@/components/light-mode-only";

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    firstName: "",
    lastName: "",
    organizationName: "",
    organizationSlug: "",
    currencyCode: "NGN",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedPlan, setSelectedPlan] = useState<{id: number, name: string, interval: 'monthly' | 'yearly'} | null>(null);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { AuthService } = await import("@/lib/auth");
        const token = AuthService.getToken();
        if (token) {
          const userData = await AuthService.getCurrentUser();
          if (userData) {
            router.push("/dashboard");
          }
        }
      } catch (error) {
        // User not authenticated, continue to show register page
      }
    };

    // Check for plan selection from URL params
    const planId = searchParams.get('plan');
    const interval = searchParams.get('interval') as 'monthly' | 'yearly';
    
    if (planId && interval) {
      const fetchPlan = async () => {
        try {
          const { SubscriptionService } = await import("@/lib/subscription-service");
          const plan = await SubscriptionService.getPlan(parseInt(planId));
          setSelectedPlan({
            id: plan.id,
            name: plan.name,
            interval: interval
          });
        } catch (error) {
          console.error('Error fetching selected plan:', error);
        }
      };
      
      fetchPlan();
    }

    checkAuth();
  }, [router, searchParams]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Auto-generate organization slug from name
    if (name === "organizationName") {
      setFormData(prev => ({
        ...prev,
        organizationSlug: value.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "")
      }));
    }
  };

  const handleCurrencyChange = (currency: Currency) => {
    setFormData(prev => ({
      ...prev,
      currencyCode: currency.code,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    // Validate passwords match
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      setIsLoading(false);
      return;
    }

    // Validate password length
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long");
      setIsLoading(false);
      return;
    }

    try {
      const { AuthService } = await import("@/lib/auth");
      const { getCurrencyByCode } = await import("@/lib/currencies");
      
      // Get full currency data
      const currency = getCurrencyByCode(formData.currencyCode);
      
      await AuthService.register({
        email: formData.email,
        password: formData.password,
        first_name: formData.firstName,
        last_name: formData.lastName,
        organization_name: formData.organizationName,
        organization_slug: formData.organizationSlug || undefined,
        currency_code: currency?.code,
        currency_symbol: currency?.symbol,
        currency_name: currency?.name,
      });
      
      // If a plan was selected, redirect to subscription page with plan info
      if (selectedPlan) {
        router.push(`/dashboard/subscription?onboard=true&plan=${selectedPlan.id}&interval=${selectedPlan.interval}`);
      } else {
        router.push("/dashboard");
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LightModeOnly>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block mb-4">
            <span className="text-2xl font-bold text-blue-600">Arvalox</span>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
          <p className="text-gray-600 mt-2">Start managing your accounts receivable today</p>
        </div>

        {/* Registration Form */}
        <Card>
          <CardHeader>
            <CardTitle>Sign Up</CardTitle>
            <CardDescription>
              Create your account and organization to get started
              {selectedPlan && (
                <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800 font-medium">
                    Selected Plan: {selectedPlan.name} ({selectedPlan.interval})
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    You'll be able to set up your subscription after creating your account.
                  </p>
                </div>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
                  {error}
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">First Name</Label>
                  <Input
                    id="firstName"
                    name="firstName"
                    type="text"
                    placeholder="John"
                    value={formData.firstName}
                    onChange={handleChange}
                    required
                    disabled={isLoading}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">Last Name</Label>
                  <Input
                    id="lastName"
                    name="lastName"
                    type="text"
                    placeholder="Doe"
                    value={formData.lastName}
                    onChange={handleChange}
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="you@company.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="organizationName">Organization Name</Label>
                <Input
                  id="organizationName"
                  name="organizationName"
                  type="text"
                  placeholder="Your Company Ltd"
                  value={formData.organizationName}
                  onChange={handleChange}
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="organizationSlug">Organization Slug</Label>
                <Input
                  id="organizationSlug"
                  name="organizationSlug"
                  type="text"
                  placeholder="your-company-ltd"
                  value={formData.organizationSlug}
                  onChange={handleChange}
                  disabled={isLoading}
                />
                <p className="text-xs text-gray-500">
                  This will be used in your organization's URL
                </p>
              </div>

              <CurrencyPicker
                label="Organization Currency"
                value={formData.currencyCode}
                onValueChange={handleCurrencyChange}
                disabled={isLoading}
                placeholder="Select your organization's currency"
              />
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a strong password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    disabled={isLoading}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Confirm Password</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    name="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    disabled={isLoading}
                    className="pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Creating account...
                  </>
                ) : (
                  "Create Account"
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Already have an account?{" "}
                <Link href="/login" className="text-blue-600 hover:text-blue-500 font-medium">
                  Sign in
                </Link>
              </p>
            </div>

            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                By creating an account, you agree to our{" "}
                <Link href="/terms" className="text-blue-600 hover:text-blue-500">
                  Terms of Service
                </Link>{" "}
                and{" "}
                <Link href="/privacy" className="text-blue-600 hover:text-blue-500">
                  Privacy Policy
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
      </div>
    </LightModeOnly>
  );
}