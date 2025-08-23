import { toast } from "@/hooks/use-toast";

export interface SubscriptionLimitError {
  isLimitError: boolean;
  limitType?: 'invoice' | 'customer' | 'team_member';
  planName?: string;
  currentLimit?: number;
  message: string;
}

export function parseSubscriptionError(error: unknown): SubscriptionLimitError {
  const message = error instanceof Error ? error.message : String(error);
  
  // Check for invoice limit error
  const invoiceLimitMatch = message.match(/Invoice limit reached\. You have reached the maximum of (\d+) invoices per month for your (.+?)\. Please upgrade/);
  if (invoiceLimitMatch) {
    return {
      isLimitError: true,
      limitType: 'invoice',
      currentLimit: parseInt(invoiceLimitMatch[1]),
      planName: invoiceLimitMatch[2],
      message: message,
    };
  }

  // Check for customer limit error
  const customerLimitMatch = message.match(/Customer limit reached\. You have reached the maximum of (\d+) customers for your (.+?)\. Please upgrade/);
  if (customerLimitMatch) {
    return {
      isLimitError: true,
      limitType: 'customer',
      currentLimit: parseInt(customerLimitMatch[1]),
      planName: customerLimitMatch[2],
      message: message,
    };
  }

  // Check for team member limit error
  const teamLimitMatch = message.match(/Team member limit reached\. You have reached the maximum of (\d+) team members for your (.+?)\. Please upgrade/);
  if (teamLimitMatch) {
    return {
      isLimitError: true,
      limitType: 'team_member',
      currentLimit: parseInt(teamLimitMatch[1]),
      planName: teamLimitMatch[2],
      message: message,
    };
  }

  return {
    isLimitError: false,
    message: message,
  };
}

export function showSubscriptionLimitError(error: unknown, onUpgradeClick?: () => void) {
  const parsedError = parseSubscriptionError(error);
  
  if (!parsedError.isLimitError) {
    // Regular error toast
    toast({
      title: "Error",
      description: parsedError.message,
      variant: "destructive",
    });
    return;
  }

  // Subscription limit error with upgrade prompt
  const limitTypeText = parsedError.limitType === 'invoice' 
    ? 'invoices' 
    : parsedError.limitType === 'customer' 
    ? 'customers' 
    : 'team members';

  const baseMessage = `You've reached your ${parsedError.planName} limit of ${parsedError.currentLimit} ${limitTypeText} per month.`;

  toast({
    title: `${limitTypeText.charAt(0).toUpperCase() + limitTypeText.slice(1)} Limit Reached`,
    description: baseMessage + (onUpgradeClick ? " Go to Subscription settings to upgrade your plan." : ""),
    variant: "destructive",
  });

  // Automatically navigate to subscription page after a short delay
  if (onUpgradeClick) {
    setTimeout(() => {
      onUpgradeClick();
    }, 3000);
  }
}