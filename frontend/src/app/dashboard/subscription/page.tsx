"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { 
  Calendar, 
  CreditCard, 
  AlertTriangle, 
  CheckCircle, 
  Clock,
  Zap,
  TrendingUp,
  Settings
} from "lucide-react";

import { PlanCard } from "@/components/subscription/plan-card";
import { UsageStatsCard } from "@/components/subscription/usage-stats";
import { 
  SubscriptionService, 
  SubscriptionSummary, 
  SubscriptionPlan,
  PlanComparison
} from "@/lib/subscription-service";
import { LoadingSpinner } from "@/components/ui/loading";
import { useToast } from "@/hooks/use-toast";
import { AuthService } from "@/lib/auth";

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
  organization_name: string;
}

export default function SubscriptionPage() {
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionSummary | null>(null);
  const [availablePlans, setAvailablePlans] = useState<SubscriptionPlan[]>([]);
  const [planComparison, setPlanComparison] = useState<PlanComparison | null>(null);
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');
  const [isLoading, setIsLoading] = useState(true);
  const [isUpgrading, setIsUpgrading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { toast } = useToast();
  const router = useRouter();

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Load user data first
      const userData = await AuthService.getCurrentUser();
      setUser(userData);

      const [currentSub, plans, comparison] = await Promise.all([
        SubscriptionService.getCurrentSubscription(),
        SubscriptionService.getPlans(),
        SubscriptionService.comparePlans().catch(() => null), // Optional, might not exist
      ]);

      setSubscription(currentSub);
      setAvailablePlans(plans);
      setPlanComparison(comparison);
      // Keep default billing interval as 'monthly' instead of using current subscription interval

    } catch (error) {
      console.error('Error loading subscription data:', error);
      setError(error instanceof Error ? error.message : 'Failed to load subscription data');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlanSelect = async (plan: SubscriptionPlan) => {
    try {
      setIsUpgrading(true);
      
      // Check if this is a free plan
      if (plan.plan_type === 'free' || 
          (billingInterval === 'monthly' && plan.monthly_price === 0) ||
          (billingInterval === 'yearly' && plan.yearly_price === 0)) {
        
        if (!subscription) {
          // Create new free subscription
          await SubscriptionService.createSubscription({
            plan_id: plan.id,
            billing_interval: billingInterval,
            start_trial: false,
            trial_days: 0,
          });
          
          toast({
            title: "Plan Activated!",
            description: `Welcome to the ${plan.name}.`,
          });
        } else {
          // Switch to free plan
          await SubscriptionService.upgradeSubscription({
            plan_id: plan.id,
            billing_interval: billingInterval,
          });
          
          toast({
            title: "Plan Updated!",
            description: `Successfully switched to ${plan.name}.`,
          });
        }
        
        // Reload data
        await loadInitialData();
        
      } else {
        // Paid plan - redirect to Paystack
        const callbackUrl = `${window.location.origin}/dashboard/subscription/payment-callback`;
        
        const paymentData = await SubscriptionService.initializePayment(
          plan.id,
          billingInterval,
          callbackUrl
        );
        
        // Store payment info in localStorage for verification later
        localStorage.setItem('pending_payment', JSON.stringify({
          reference: paymentData.reference,
          plan_id: plan.id,
          billing_interval: billingInterval,
          plan_name: plan.name
        }));
        
        // Redirect to Paystack
        SubscriptionService.redirectToPaystack(paymentData.authorization_url);
      }

    } catch (error) {
      console.error('Error updating subscription:', error);
      toast({
        variant: "destructive",
        title: "Update Failed",
        description: error instanceof Error ? error.message : "Failed to update subscription",
      });
      setIsUpgrading(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (!subscription) return;
    
    if (!confirm('Are you sure you want to cancel your subscription? It will remain active until the end of your current billing period.')) {
      return;
    }

    try {
      await SubscriptionService.cancelSubscription({
        cancel_immediately: false,
        reason: 'User requested cancellation',
      });
      
      toast({
        title: "Subscription Cancelled",
        description: "Your subscription will remain active until the end of your current billing period.",
      });
      
      await loadInitialData();
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      toast({
        variant: "destructive",
        title: "Cancellation Failed",
        description: error instanceof Error ? error.message : "Failed to cancel subscription",
      });
    }
  };

  const handleReactivateSubscription = async () => {
    if (!subscription) return;
    
    if (!confirm('Are you sure you want to reactivate your subscription? Billing will resume according to your current plan.')) {
      return;
    }

    try {
      setIsUpgrading(true);
      await SubscriptionService.reactivateSubscription();
      
      toast({
        title: "Subscription Reactivated",
        description: "Your subscription has been successfully reactivated.",
      });
      
      await loadInitialData();
    } catch (error) {
      console.error('Error reactivating subscription:', error);
      toast({
        variant: "destructive",
        title: "Reactivation Failed",
        description: error instanceof Error ? error.message : "Failed to reactivate subscription",
      });
    } finally {
      setIsUpgrading(false);
    }
  };

  const handleCancelDowngrade = async () => {
    if (!subscription) return;
    
    if (!confirm('Are you sure you want to cancel the scheduled downgrade? You will remain on your current plan.')) {
      return;
    }

    try {
      setIsUpgrading(true);
      await SubscriptionService.cancelScheduledDowngrade();
      
      toast({
        title: "Downgrade Cancelled",
        description: "Your scheduled downgrade has been cancelled. You'll remain on your current plan.",
      });
      
      await loadInitialData();
    } catch (error) {
      console.error('Error cancelling downgrade:', error);
      toast({
        variant: "destructive",
        title: "Cancellation Failed",
        description: error instanceof Error ? error.message : "Failed to cancel downgrade",
      });
    } finally {
      setIsUpgrading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error && !subscription) {
    return (
      <DashboardLayout user={user}>
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Subscription</h1>
            <p className="text-muted-foreground">Manage your subscription and billing</p>
          </div>
          
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          
          <Button onClick={loadInitialData}>Try Again</Button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Subscription</h1>
          <p className="text-muted-foreground">Manage your subscription and billing</p>
        </div>
        
        {subscription && (
          <Button variant="outline" onClick={() => router.push('/dashboard/settings')}>
            <Settings className="w-4 h-4 mr-2" />
            Billing Settings
          </Button>
        )}
      </div>

      {subscription && (
        <>
          {/* Current Subscription Overview */}
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CreditCard className="w-5 h-5" />
                  <span>Current Plan</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg">{subscription.subscription.plan.name}</h3>
                    <p className="text-muted-foreground text-sm">
                      {SubscriptionService.formatPrice(
                        subscription.subscription.billing_interval === 'yearly' 
                          ? subscription.subscription.plan.yearly_price 
                          : subscription.subscription.plan.monthly_price,
                        subscription.subscription.plan.currency
                      )}
                      /{subscription.subscription.billing_interval}
                    </p>
                  </div>
                  
                  <Badge 
                    className={`capitalize ${
                      subscription.subscription.status === 'active' ? 'bg-green-100 text-green-800' :
                      subscription.subscription.status === 'trialing' ? 'bg-blue-100 text-blue-800' :
                      subscription.subscription.status === 'canceled' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {subscription.subscription.status}
                  </Badge>
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground flex items-center">
                      <Calendar className="w-4 h-4 mr-2" />
                      Current Period
                    </span>
                    <span>
                      {formatDate(subscription.subscription.current_period_start)} - {formatDate(subscription.subscription.current_period_end)}
                    </span>
                  </div>

                  {subscription.subscription.is_trialing && subscription.subscription.trial_end && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground flex items-center">
                        <Clock className="w-4 h-4 mr-2" />
                        Trial Ends
                      </span>
                      <span className="font-medium">
                        {formatDate(subscription.subscription.trial_end)}
                        {subscription.subscription.days_until_expiry !== null && (
                          <span className="ml-1 text-blue-600">
                            ({subscription.subscription.days_until_expiry} days left)
                          </span>
                        )}
                      </span>
                    </div>
                  )}

                  {subscription.subscription.next_payment_date && !subscription.subscription.is_downgrading && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground flex items-center">
                        <CreditCard className="w-4 h-4 mr-2" />
                        Next Payment
                      </span>
                      <span>{formatDate(subscription.subscription.next_payment_date)}</span>
                    </div>
                  )}

                  {subscription.subscription.is_downgrading && subscription.subscription.downgrade_effective_date && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground flex items-center">
                        <Clock className="w-4 h-4 mr-2" />
                        Downgrading On
                      </span>
                      <span className="text-yellow-600 dark:text-yellow-400 font-medium">
                        {formatDate(subscription.subscription.downgrade_effective_date)}
                        {subscription.subscription.downgrade_days_remaining !== null && (
                          <span className="ml-1">
                            ({subscription.subscription.downgrade_days_remaining} days)
                          </span>
                        )}
                      </span>
                    </div>
                  )}
                </div>

                {subscription.subscription.is_downgrading && subscription.subscription.downgrade_effective_date && (
                  <div className="space-y-3">
                    <Alert>
                      <Clock className="h-4 w-4" />
                      <AlertDescription>
                        Scheduled to downgrade to Free Plan on {formatDate(subscription.subscription.downgrade_effective_date)}.
                        You'll keep all current features until then.
                      </AlertDescription>
                    </Alert>
                    <Button 
                      onClick={handleCancelDowngrade}
                      disabled={isUpgrading}
                      variant="outline"
                      className="w-full"
                    >
                      {isUpgrading ? "Cancelling..." : "Cancel Downgrade"}
                    </Button>
                  </div>
                )}

                {subscription.subscription.status === 'canceled' && subscription.subscription.canceled_at && (
                  <div className="space-y-3">
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        Subscription cancelled on {formatDate(subscription.subscription.canceled_at)}. 
                        Access continues until {formatDate(subscription.subscription.current_period_end)}.
                      </AlertDescription>
                    </Alert>
                    <Button 
                      onClick={handleReactivateSubscription}
                      disabled={isUpgrading}
                      className="w-full"
                    >
                      {isUpgrading ? "Reactivating..." : "Reactivate Subscription"}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Usage Stats */}
            <UsageStatsCard stats={subscription.usage_stats} />
          </div>

          {/* Trial Warning */}
          {subscription.subscription.is_trialing && subscription.subscription.days_until_expiry !== null && subscription.subscription.days_until_expiry <= 7 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Your free trial expires in {subscription.subscription.days_until_expiry} days. 
                Choose a plan below to continue using Arvalox without interruption.
              </AlertDescription>
            </Alert>
          )}
          {/* Scheduled Downgrade Alert */}
          {subscription.subscription.is_downgrading && subscription.subscription.downgrade_effective_date && (
            <Alert>
              <Clock className="h-4 w-4" />
              <AlertDescription>
                Your plan will downgrade to Free Plan on {formatDate(subscription.subscription.downgrade_effective_date)}
                {subscription.subscription.downgrade_days_remaining !== null && (
                  <span className="font-medium">
                    {' '}({subscription.subscription.downgrade_days_remaining} days remaining)
                  </span>
                )}
                . You'll keep all current features until then.
              </AlertDescription>
            </Alert>
          )}
        </>
      )}

      {/* Plan Selection */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">
              {subscription ? 'Upgrade Your Plan' : 'Choose Your Plan'}
            </h2>
            <p className="text-muted-foreground">
              {subscription ? 'Compare plans and upgrade for more features' : 'Select the perfect plan for your business needs'}
            </p>
          </div>

          <Tabs value={billingInterval} onValueChange={(value) => setBillingInterval(value as 'monthly' | 'yearly')}>
            <TabsList>
              <TabsTrigger value="monthly">Monthly</TabsTrigger>
              <TabsTrigger value="yearly">Yearly</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {availablePlans.filter(plan => plan.is_active).map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              subscription={subscription?.subscription}
              isCurrentPlan={subscription?.subscription.plan.id === plan.id}
              isPopular={plan.plan_type === 'professional'} // Mark professional as popular
              billingInterval={billingInterval}
              onSelectPlan={handlePlanSelect}
              isLoading={isUpgrading}
              disabled={isUpgrading}
            />
          ))}
        </div>

        {subscription && subscription.subscription.status !== 'canceled' && (
          <div className="flex justify-center pt-6">
            <Button 
              variant="destructive" 
              onClick={handleCancelSubscription}
              size="sm"
            >
              Cancel Subscription
            </Button>
          </div>
        )}
      </div>
      </div>
    </DashboardLayout>
  );
}