"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, CheckCircle, Clock, CreditCard } from "lucide-react";
import { SubscriptionSummary } from "@/lib/subscription-service";

interface SubscriptionStatusProps {
  subscription: SubscriptionSummary;
}

export function SubscriptionStatus({ subscription }: SubscriptionStatusProps) {
  const { subscription: sub, usage_stats } = subscription;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'trialing':
        return <Clock className="w-4 h-4 text-blue-600" />;
      case 'canceled':
      case 'past_due':
        return <AlertTriangle className="w-4 h-4 text-red-600" />;
      default:
        return <CreditCard className="w-4 h-4 text-gray-600" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'trialing':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'canceled':
      case 'past_due':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  // Check if approaching any limits
  const isApproachingLimits = 
    (usage_stats.invoice_usage_percentage && usage_stats.invoice_usage_percentage >= 80) ||
    (usage_stats.customer_usage_percentage && usage_stats.customer_usage_percentage >= 80) ||
    (usage_stats.team_member_usage_percentage && usage_stats.team_member_usage_percentage >= 80);

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Subscription Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Status Badge */}
        <div className="flex items-center space-x-2">
          {getStatusIcon(sub.status)}
          <Badge className={`capitalize ${getStatusColor(sub.status)}`}>
            {sub.status}
          </Badge>
          <span className="text-sm font-medium">{sub.plan.name}</span>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="text-center">
            <div className="font-medium text-gray-900">{usage_stats.current_invoice_count}</div>
            <div className="text-muted-foreground">Invoices</div>
          </div>
          <div className="text-center">
            <div className="font-medium text-gray-900">{usage_stats.current_customer_count}</div>
            <div className="text-muted-foreground">Customers</div>
          </div>
          <div className="text-center">
            <div className="font-medium text-gray-900">{usage_stats.current_team_member_count}</div>
            <div className="text-muted-foreground">Team</div>
          </div>
        </div>

        {/* Trial Warning */}
        {sub.is_trialing && sub.days_until_expiry !== null && sub.days_until_expiry <= 7 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-2">
            <div className="flex items-center space-x-2">
              <Clock className="w-3 h-3 text-yellow-600" />
              <span className="text-xs text-yellow-800 font-medium">
                Trial ends in {sub.days_until_expiry} days
              </span>
            </div>
          </div>
        )}

        {/* Usage Warning */}
        {isApproachingLimits && (
          <div className="bg-orange-50 border border-orange-200 rounded-md p-2">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-3 h-3 text-orange-600" />
              <span className="text-xs text-orange-800 font-medium">
                Approaching usage limits
              </span>
            </div>
          </div>
        )}

        {/* Next Billing */}
        {sub.next_payment_date && sub.status === 'active' && (
          <div className="text-xs text-muted-foreground">
            Next billing: {formatDate(sub.next_payment_date)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}