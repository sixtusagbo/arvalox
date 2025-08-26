"use client";

import { useState, useEffect } from "react";
import { PlanCard } from "@/components/subscription/plan-card";
import { SubscriptionPlan, SubscriptionService } from "@/lib/subscription-service";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";

interface PricingSectionProps {
  showHeader?: boolean;
  className?: string;
}

export function PricingSection({ showHeader = true, className = "" }: PricingSectionProps) {
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        setLoading(true);
        setError(null);
        const fetchedPlans = await SubscriptionService.getPlans();
        // Sort plans by sort_order to ensure consistent display
        const sortedPlans = fetchedPlans
          .filter(plan => plan.is_active)
          .sort((a, b) => a.sort_order - b.sort_order);
        setPlans(sortedPlans);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load pricing plans');
        console.error('Error fetching subscription plans:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  if (loading) {
    return (
      <section className={`py-20 ${className}`}>
        <div className="container mx-auto px-4">
          {showHeader && (
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Choose Your Plan
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Flexible pricing to scale with your business needs
              </p>
            </div>
          )}
          <div className="flex justify-center items-center min-h-[400px]">
            <div className="flex items-center space-x-2">
              <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
              <span className="text-lg text-gray-600">Loading pricing plans...</span>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className={`py-20 ${className}`}>
        <div className="container mx-auto px-4">
          {showHeader && (
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Choose Your Plan
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Flexible pricing to scale with your business needs
              </p>
            </div>
          )}
          <div className="flex justify-center items-center min-h-[400px]">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button 
                onClick={() => window.location.reload()} 
                variant="outline"
              >
                Try Again
              </Button>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (plans.length === 0) {
    return (
      <section className={`py-20 ${className}`}>
        <div className="container mx-auto px-4">
          {showHeader && (
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
                Choose Your Plan
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Flexible pricing to scale with your business needs
              </p>
            </div>
          )}
          <div className="flex justify-center items-center min-h-[400px]">
            <p className="text-gray-600 text-lg">No pricing plans available at the moment.</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={`py-20 ${className}`}>
      <div className="container mx-auto px-4">
        {showHeader && (
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Choose Your Plan
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Flexible pricing to scale with your business needs. All plans include our core AR features.
            </p>
          </div>
        )}

        {/* Billing Toggle */}
        <div className="flex justify-center mb-12">
          <div className="flex items-center bg-gray-100 rounded-lg p-1">
            <Button
              variant={billingInterval === 'monthly' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setBillingInterval('monthly')}
              className="relative"
            >
              Monthly
            </Button>
            <Button
              variant={billingInterval === 'yearly' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setBillingInterval('yearly')}
              className="relative"
            >
              Yearly
              <Badge className="absolute -top-2 -right-2 bg-green-600 text-white text-xs px-1 py-0.5">
                Save 20%
              </Badge>
            </Button>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-7xl mx-auto">
          {plans.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              billingInterval={billingInterval}
              isPopular={plan.plan_type === 'professional'}
              onSelectPlan={(selectedPlan) => {
                // Redirect to register page with plan selection
                const planParam = `?plan=${selectedPlan.id}&interval=${billingInterval}`;
                window.location.href = `/register${planParam}`;
              }}
            />
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-16">
          <p className="text-gray-600 mb-6">
            Need a custom solution for your enterprise? 
          </p>
          <Button variant="outline" size="lg">
            Contact Sales
          </Button>
        </div>

        {/* Features Comparison */}
        <div className="mt-20">
          <h3 className="text-2xl font-bold text-center text-gray-900 mb-8">
            All plans include
          </h3>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 className="font-semibold text-gray-900">SSL Security</h4>
              <p className="text-sm text-gray-600">Bank-level encryption</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 className="font-semibold text-gray-900">24/7 Uptime</h4>
              <p className="text-sm text-gray-600">99.9% availability</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
              </div>
              <h4 className="font-semibold text-gray-900">Data Backup</h4>
              <p className="text-sm text-gray-600">Automatic daily backups</p>
            </div>
            
            <div className="text-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 className="font-semibold text-gray-900">Support</h4>
              <p className="text-sm text-gray-600">Email & chat support</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}