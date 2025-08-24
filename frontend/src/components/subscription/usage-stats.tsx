"use client";

import { Progress } from "@/components/ui/progress";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Users, UserPlus, AlertTriangle, CheckCircle, Info } from "lucide-react";
import { UsageStats, SubscriptionService } from "@/lib/subscription-service";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface UsageStatsProps {
  stats: UsageStats;
}

export function UsageStatsCard({ stats }: UsageStatsProps) {
  const usageItems = [
    {
      label: "Invoices",
      icon: FileText,
      current: stats.current_invoice_count,
      max: stats.max_invoices_per_month,
      percentage: stats.invoice_usage_percentage,
      canPerform: stats.can_create_invoice,
      unlimited: stats.max_invoices_per_month === null,
      resetMonthly: true,
    },
    {
      label: "Customers",
      icon: Users,
      current: stats.current_customer_count,
      max: stats.max_customers,
      percentage: stats.customer_usage_percentage,
      canPerform: stats.can_add_customer,
      unlimited: stats.max_customers === null,
      resetMonthly: false,
    },
    {
      label: "Team Members",
      icon: UserPlus,
      current: stats.current_team_member_count,
      max: stats.max_team_members,
      percentage: stats.team_member_usage_percentage,
      canPerform: stats.can_add_team_member,
      unlimited: stats.max_team_members === null,
      resetMonthly: false,
    },
  ];

  return (
    <TooltipProvider>
      <Card>
        <CardHeader>
          <CardTitle className="text-lg font-semibold">Usage Statistics</CardTitle>
          <CardDescription>
            Current usage for your subscription plan this month
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
        {usageItems.map((item, index) => {
          const Icon = item.icon;
          const percentage = item.percentage || 0;
          const isNearLimit = percentage >= 80 && !item.unlimited;
          const isAtLimit = percentage >= 100 && !item.unlimited;

          return (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Icon className="w-4 h-4 text-gray-600 dark:text-gray-300" />
                  <span className="font-medium text-sm">{item.label}</span>
                  {item.resetMonthly && (
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="w-3 h-3 text-blue-500 cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="text-xs">Resets monthly on your billing cycle date</p>
                      </TooltipContent>
                    </Tooltip>
                  )}
                  {item.canPerform ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                  )}
                </div>
                
                <div className="text-right">
                  <span className="text-sm font-medium">
                    {item.current.toLocaleString()}
                    {!item.unlimited && (
                      <>
                        {" / "}
                        <span className="text-muted-foreground">
                          {item.max?.toLocaleString()}
                        </span>
                      </>
                    )}
                  </span>
                  
                  <div className="flex items-center space-x-2">
                    <Badge 
                      variant="outline" 
                      className={`text-xs ${SubscriptionService.getUsageColor(item.percentage)}`}
                    >
                      {SubscriptionService.formatUsagePercentage(item.percentage, item.unlimited)}
                    </Badge>
                  </div>
                </div>
              </div>

              {!item.unlimited && (
                <div className="space-y-1">
                  <Progress 
                    value={Math.min(percentage, 100)} 
                    className="h-2"
                  />
                  
                  {isAtLimit && (
                    <p className="text-xs text-red-600 font-medium">
                      Limit reached - upgrade your plan to continue
                    </p>
                  )}
                  
                  {isNearLimit && !isAtLimit && (
                    <p className="text-xs text-yellow-600 font-medium">
                      Approaching limit - consider upgrading soon
                    </p>
                  )}
                </div>
              )}

              {item.unlimited && (
                <div className="flex items-center space-x-1">
                  <div className="h-2 bg-green-200 rounded-full flex-1">
                    <div className="h-full bg-green-600 rounded-full" style={{ width: "20%" }} />
                  </div>
                  <span className="text-xs text-green-600 font-medium">Unlimited</span>
                </div>
              )}
            </div>
          );
        })}

        <div className="pt-4 border-t">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Overall Status</span>
            <Badge 
              variant={stats.can_create_invoice && stats.can_add_customer ? "default" : "destructive"}
              className="text-xs"
            >
              {stats.can_create_invoice && stats.can_add_customer ? "All Systems Go" : "Action Required"}
            </Badge>
          </div>
          
          {(!stats.can_create_invoice || !stats.can_add_customer || !stats.can_add_team_member) && (
            <p className="text-xs text-muted-foreground mt-2">
              Some features are limited. Consider upgrading your plan for full access.
            </p>
          )}
        </div>
        </CardContent>
      </Card>
    </TooltipProvider>
  );
}