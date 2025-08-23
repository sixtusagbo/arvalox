'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Edit, Trash2, DollarSign, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { LoadingState } from '@/components/ui/loading';
import { PaymentService, Payment } from '@/lib/payments';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function PaymentViewPage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const params = useParams();
  const [payment, setPayment] = useState<Payment | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const { toast } = useToast();

  const paymentId = parseInt(params.id as string);

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
    const loadPayment = async () => {
      if (!paymentId || isNaN(paymentId)) {
        router.push('/dashboard/payments');
        return;
      }

      try {
        setLoading(true);
        const paymentData = await PaymentService.getPayment(paymentId);
        setPayment(paymentData);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to load payment',
          variant: 'destructive',
        });
        router.push('/dashboard/payments');
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      loadPayment();
    }
  }, [user, paymentId, router, toast]);

  const handleDeletePayment = async () => {
    if (!payment) return;

    try {
      await PaymentService.deletePayment(payment.id);
      setIsDeleteDialogOpen(false);
      toast({
        title: 'Success',
        description: 'Payment deleted successfully',
      });
      router.push('/dashboard/payments');
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete payment',
        variant: 'destructive',
      });
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'pending':
        return 'secondary';
      case 'failed':
        return 'destructive';
      case 'cancelled':
        return 'outline';
      default:
        return 'outline';
    }
  };

  if (!user) {
    return <LoadingState />;
  }

  if (loading) {
    return (
      <DashboardLayout user={user}>
        <div className="flex-1 p-4 md:p-8 pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading payment...</div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!payment) {
    return (
      <DashboardLayout user={user}>
        <div className="flex-1 p-4 md:p-8 pt-6">
          <div className="text-center">
            <p className="text-muted-foreground">Payment not found</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" onClick={() => router.back()}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <div>
              <h2 className="text-3xl font-bold tracking-tight">Payment Details</h2>
              <p className="text-muted-foreground">
                Recorded on {PaymentService.formatDate(payment.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {payment.invoice && (
              <Button variant="outline" onClick={() => router.push(`/dashboard/invoices/${payment.invoice?.id}`)}>
                <FileText className="mr-2 h-4 w-4" />
                View Invoice
              </Button>
            )}
            {payment.status === 'pending' && (
              <Button onClick={() => router.push(`/dashboard/payments/${payment.id}/edit`)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            {/* Payment Details */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Payment Information</CardTitle>
                    <CardDescription>Basic payment details</CardDescription>
                  </div>
                  <Badge variant={getStatusBadgeVariant(payment.status)}>
                    {PaymentService.formatPaymentStatus(payment.status)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Amount</h4>
                    <p className="text-2xl font-bold text-green-600 mt-1">
                      {PaymentService.formatCurrency(payment.amount)}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Payment Method</h4>
                    <p className="font-medium mt-1">
                      {PaymentService.formatPaymentMethod(payment.payment_method)}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Payment Date</h4>
                    <p className="font-medium mt-1">
                      {PaymentService.formatDate(payment.payment_date)}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Reference Number</h4>
                    <p className="font-medium mt-1">
                      {payment.reference_number || 'N/A'}
                    </p>
                  </div>
                </div>
                
                {payment.notes && (
                  <div className="mt-4">
                    <h4 className="font-medium text-sm text-muted-foreground">Notes</h4>
                    <p className="mt-1 text-sm">{payment.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Invoice Details */}
            {payment.invoice && (
              <Card>
                <CardHeader>
                  <CardTitle>Related Invoice</CardTitle>
                  <CardDescription>Invoice this payment was applied to</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Invoice Number:</span>
                      <span className="font-medium">{payment.invoice.invoice_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Customer:</span>
                      <span className="font-medium">{payment.invoice.customer_name || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Invoice Total:</span>
                      <span className="font-medium">
                        {PaymentService.formatCurrency(payment.invoice.total_amount)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="mt-4">
                    <Button 
                      variant="outline" 
                      className="w-full"
                      onClick={() => router.push(`/dashboard/invoices/${payment.invoice?.id}`)}
                    >
                      <FileText className="mr-2 h-4 w-4" />
                      View Full Invoice
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Actions */}
          <div className="lg:col-span-1 space-y-6">
            {/* Payment Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <DollarSign className="mr-2 h-4 w-4" />
                  Payment Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Payment Amount:</span>
                    <span className="font-medium text-green-600">
                      {PaymentService.formatCurrency(payment.amount)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <Badge variant={getStatusBadgeVariant(payment.status)}>
                      {PaymentService.formatPaymentStatus(payment.status)}
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>Method:</span>
                    <span>{PaymentService.formatPaymentMethod(payment.payment_method)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {payment.invoice && (
                  <Button variant="outline" className="w-full" onClick={() => router.push(`/dashboard/invoices/${payment.invoice?.id}`)}>
                    <FileText className="mr-2 h-4 w-4" />
                    View Invoice
                  </Button>
                )}
                {payment.status === 'pending' && (
                  <Button variant="outline" className="w-full" onClick={() => router.push(`/dashboard/payments/${payment.id}/edit`)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit Payment
                  </Button>
                )}
                {(payment.status === 'pending' || payment.status === 'failed') && (
                  <Button 
                    variant="outline" 
                    className="w-full text-red-600 border-red-200 hover:bg-red-50"
                    onClick={() => setIsDeleteDialogOpen(true)}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete Payment
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Delete Dialog */}
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Payment</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete this payment? 
                This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDeletePayment}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}