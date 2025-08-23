"use client";

import { Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SubscriptionPlan, SubscriptionService } from "@/lib/subscription-service";

interface PlanCardProps {
  plan: SubscriptionPlan;
  isCurrentPlan?: boolean;
  isPopular?: boolean;
  billingInterval: 'monthly' | 'yearly';
  onSelectPlan?: (plan: SubscriptionPlan) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export function PlanCard({
  plan,
  isCurrentPlan = false,
  isPopular = false,
  billingInterval,
  onSelectPlan,
  isLoading = false,
  disabled = false,
}: PlanCardProps) {
  const price = billingInterval === 'yearly' ? plan.yearly_price : plan.monthly_price;
  const monthlyPrice = billingInterval === 'yearly' ? plan.yearly_price / 12 : plan.monthly_price;
  
  const features = [
    {
      name: "Invoices per month",
      value: plan.max_invoices_per_month,
      unlimited: plan.max_invoices_per_month === null,
    },
    {
      name: "Customers",
      value: plan.max_customers,
      unlimited: plan.max_customers === null,
    },
    {
      name: "Team members",
      value: plan.max_team_members,
      unlimited: plan.max_team_members === null,
    },
    {
      name: "API access",
      included: plan.api_access,
    },
    {
      name: "Advanced reporting",
      included: plan.advanced_reporting,
    },
    {
      name: "Custom branding",
      included: plan.custom_branding,
    },
    {
      name: "Multi-currency support",
      included: plan.multi_currency,
    },
    {
      name: "Priority support",
      included: plan.priority_support,
    },
  ];

  const planColors = SubscriptionService.getPlanColor(plan.plan_type);

  return (
    <Card className={`relative flex flex-col ${isPopular ? 'border-blue-500 shadow-lg' : ''} ${isCurrentPlan ? 'ring-2 ring-blue-500' : ''}`}>
      {isPopular && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <Badge className="bg-blue-600 text-white">Most Popular</Badge>
        </div>
      )}
      
      {isCurrentPlan && (
        <div className="absolute -top-3 right-4">
          <Badge className="bg-green-600 text-white">Current Plan</Badge>
        </div>
      )}

      <CardHeader className="text-center pb-4">
        <CardTitle className="text-xl font-bold">{plan.name}</CardTitle>
        {plan.description && (
          <CardDescription className="text-sm text-muted-foreground">
            {plan.description}
          </CardDescription>
        )}
        
        <div className="mt-4">
          <div className="flex items-baseline justify-center">
            <span className="text-3xl font-bold">
              {SubscriptionService.formatPrice(price, plan.currency)}
            </span>
            {price > 0 && (
              <span className="text-muted-foreground ml-1">
                /{billingInterval}
              </span>
            )}
          </div>
          
          {billingInterval === 'yearly' && price > 0 && (
            <p className="text-sm text-muted-foreground mt-1">
              {SubscriptionService.formatPrice(monthlyPrice, plan.currency)}/month billed annually
            </p>
          )}
          
          {billingInterval === 'yearly' && price > 0 && plan.monthly_price > 0 && (
            <p className="text-sm text-green-600 font-medium mt-1">
              Save {SubscriptionService.formatPrice((plan.monthly_price * 12) - plan.yearly_price, plan.currency)} per year
            </p>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col">
        <ul className="space-y-3 flex-1">
          {features.map((feature, index) => {
            const isIncluded = 'included' in feature ? feature.included : true;
            
            return (
              <li key={index} className="flex items-start">
                <div className="flex-shrink-0 mt-0.5">
                  {isIncluded ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <X className="w-4 h-4 text-gray-400" />
                  )}
                </div>
                <div className="ml-3 flex-1">
                  <span className={`text-sm ${isIncluded ? 'text-gray-900' : 'text-gray-400'}`}>
                    {feature.name}
                  </span>
                  {'value' in feature && (
                    <span className="ml-2 text-sm font-medium">
                      {feature.unlimited ? 'Unlimited' : feature.value?.toLocaleString()}
                    </span>
                  )}
                </div>
              </li>
            );
          })}
        </ul>

        <div className="mt-6">
          <Button
            className="w-full"
            variant={isCurrentPlan ? "outline" : "default"}
            onClick={() => onSelectPlan?.(plan)}
            disabled={disabled || isLoading || isCurrentPlan}
          >
            {isLoading ? (
              <div className="flex items-center">
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                Processing...
              </div>
            ) : isCurrentPlan ? (
              'Current Plan'
            ) : (
              `Choose ${plan.name}`
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}