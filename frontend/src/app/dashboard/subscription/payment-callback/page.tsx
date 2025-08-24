'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { DashboardLayout } from '@/components/dashboard-layout';
import { LoadingState } from '@/components/ui/loading';
import { SubscriptionService } from '@/lib/subscription-service';
import { AuthService } from '@/lib/auth';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function PaymentCallbackPage() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('');
  const [planName, setPlanName] = useState('');
  
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const { AuthService } = await import("@/lib/auth");
        const token = AuthService.getToken();
        if (!token) {
          router.push("/login");
          return;
        }

        const userData = await AuthService.getCurrentUser();
        if (!userData) {
          router.push("/login");
          return;
        }
        setUser(userData);
      } catch (error) {
        console.error("Error checking auth:", error);
        router.push("/login");
      }
    };

    checkAuth();
  }, [router]);

  useEffect(() => {
    if (!user) return;
    
    const processPayment = async () => {
      try {
        // Get reference from URL params
        const reference = searchParams.get('reference');
        
        if (!reference) {
          setStatus('error');
          setMessage('Payment reference not found');
          setLoading(false);
          return;
        }

        // Get stored payment info
        const storedPayment = localStorage.getItem('pending_payment');
        if (!storedPayment) {
          setStatus('error');
          setMessage('Payment information not found');
          setLoading(false);
          return;
        }

        const paymentInfo = JSON.parse(storedPayment);
        setPlanName(paymentInfo.plan_name);

        // Verify payment with backend
        await SubscriptionService.verifyPayment(
          reference,
          paymentInfo.plan_id,
          paymentInfo.billing_interval
        );

        // Clear stored payment info
        localStorage.removeItem('pending_payment');

        setStatus('success');
        setMessage('Payment successful! Your subscription has been activated.');
        
        // Redirect to subscription page after 3 seconds
        setTimeout(() => {
          router.push('/dashboard/subscription');
        }, 3000);

      } catch (error) {
        console.error('Payment verification error:', error);
        setStatus('error');
        setMessage(error instanceof Error ? error.message : 'Payment verification failed');
      } finally {
        setLoading(false);
      }
    };

    processPayment();
  }, [user, searchParams, router]);

  if (!user) {
    return <LoadingState message="Loading..." />;
  }

  if (loading) {
    return (
      <DashboardLayout user={user}>
        <div className="flex-1 p-4 md:p-8 pt-6">
          <div className="max-w-md mx-auto">
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
                <p className="text-lg font-medium">Processing Payment...</p>
                <p className="text-muted-foreground text-center mt-2">
                  Please wait while we verify your payment with Paystack.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="flex-1 p-4 md:p-8 pt-6">
        <div className="max-w-md mx-auto">
          <Card>
            <CardHeader className="text-center">
              <div className="flex justify-center mb-4">
                {status === 'success' ? (
                  <CheckCircle className="h-16 w-16 text-green-600" />
                ) : (
                  <XCircle className="h-16 w-16 text-red-600" />
                )}
              </div>
              <CardTitle className={`text-2xl ${status === 'success' ? 'text-green-600' : 'text-red-600'}`}>
                {status === 'success' ? 'Payment Successful!' : 'Payment Failed'}
              </CardTitle>
              <CardDescription className="text-base">
                {planName && status === 'success' && (
                  <>Welcome to {planName}!</>
                )}
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p className="text-muted-foreground">
                {message}
              </p>
              
              {status === 'success' ? (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    You will be redirected to your subscription dashboard in a few seconds.
                  </p>
                  <Button 
                    onClick={() => router.push('/dashboard/subscription')}
                    className="w-full"
                  >
                    Go to Subscription Dashboard
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Don't worry, your payment was not charged if the verification failed.
                  </p>
                  <Button 
                    onClick={() => router.push('/dashboard/subscription')}
                    variant="outline"
                    className="w-full"
                  >
                    Back to Plans
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}