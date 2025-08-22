'use client';

import { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Save, DollarSign } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { PaymentService, PaymentCreate } from '@/lib/payments';
import { InvoiceService, Invoice } from '@/lib/invoices';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function NewPaymentPage() {
  const [user, setUser] = useState<User | null>(null);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  const [paymentData, setPaymentData] = useState<PaymentCreate>({
    invoice_id: 0,
    payment_date: new Date().toISOString().split('T')[0],
    amount: 0,
    payment_method: 'cash',
    reference_number: '',
    notes: '',
  });

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
    if (user) {
      loadUnpaidInvoices();
    }
  }, [user]);

  // Handle pre-selected invoice from query params
  useEffect(() => {
    const invoiceParam = searchParams.get('invoice');
    if (invoiceParam && invoices.length > 0) {
      handleInvoiceSelect(invoiceParam);
    }
  }, [invoices, searchParams]);

  const loadUnpaidInvoices = async () => {
    try {
      setLoading(true);
      const response = await InvoiceService.getInvoices({
        status: 'sent', // Only sent invoices can receive payments
        per_page: 100,
      });
      
      // Filter invoices that still have outstanding balances
      const unpaidInvoices = response.invoices.filter(invoice => {
        const balance = invoice.total_amount - invoice.paid_amount;
        return balance > 0;
      });
      
      setInvoices(unpaidInvoices);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load invoices',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInvoiceSelect = (invoiceId: string) => {
    const invoice = invoices.find(inv => inv.id === parseInt(invoiceId));
    setSelectedInvoice(invoice || null);
    
    if (invoice) {
      const outstandingBalance = invoice.total_amount - invoice.paid_amount;
      setPaymentData(prev => ({
        ...prev,
        invoice_id: invoice.id,
        amount: outstandingBalance,
      }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!paymentData.invoice_id) {
      toast({
        title: 'Error',
        description: 'Please select an invoice',
        variant: 'destructive',
      });
      return;
    }

    if (!paymentData.amount || paymentData.amount <= 0) {
      toast({
        title: 'Error',
        description: 'Please enter a valid payment amount',
        variant: 'destructive',
      });
      return;
    }

    if (selectedInvoice) {
      const outstandingBalance = selectedInvoice.total_amount - selectedInvoice.paid_amount;
      if (paymentData.amount > outstandingBalance) {
        toast({
          title: 'Error',
          description: `Payment amount cannot exceed outstanding balance of ${InvoiceService.formatCurrency(outstandingBalance)}`,
          variant: 'destructive',
        });
        return;
      }
    }

    try {
      setSaving(true);
      const payment = await PaymentService.createPayment(paymentData);
      
      toast({
        title: 'Success',
        description: 'Payment recorded successfully',
      });

      router.push('/dashboard/payments');
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to record payment',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <DashboardLayout user={user}>
        <div className="flex-1 p-4 md:p-8 pt-6">
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading invoices...</div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h2 className="text-3xl font-bold tracking-tight">Record New Payment</h2>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit}>
              <Card>
                <CardHeader>
                  <CardTitle>Payment Details</CardTitle>
                  <CardDescription>Enter payment information</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="invoice">Invoice *</Label>
                    <Select
                      value={paymentData.invoice_id.toString()}
                      onValueChange={handleInvoiceSelect}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select an invoice" />
                      </SelectTrigger>
                      <SelectContent>
                        {invoices.map((invoice) => (
                          <SelectItem key={invoice.id} value={invoice.id.toString()}>
                            {invoice.invoice_number} - {invoice.customer?.name} 
                            ({InvoiceService.formatCurrency(invoice.total_amount - invoice.paid_amount)} outstanding)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="payment_date">Payment Date *</Label>
                      <Input
                        id="payment_date"
                        type="date"
                        value={paymentData.payment_date}
                        onChange={(e) => setPaymentData(prev => ({ ...prev, payment_date: e.target.value }))}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="amount">Amount *</Label>
                      <Input
                        id="amount"
                        type="number"
                        min="0"
                        step="0.01"
                        value={paymentData.amount}
                        onChange={(e) => setPaymentData(prev => ({ ...prev, amount: parseFloat(e.target.value) || 0 }))}
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="payment_method">Payment Method *</Label>
                      <Select
                        value={paymentData.payment_method}
                        onValueChange={(value) => setPaymentData(prev => ({ ...prev, payment_method: value }))}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="cash">Cash</SelectItem>
                          <SelectItem value="check">Check</SelectItem>
                          <SelectItem value="bank_transfer">Bank Transfer</SelectItem>
                          <SelectItem value="credit_card">Credit Card</SelectItem>
                          <SelectItem value="online">Online Payment</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="reference_number">Reference Number</Label>
                      <Input
                        id="reference_number"
                        placeholder="Check #, transaction ID, etc."
                        value={paymentData.reference_number}
                        onChange={(e) => setPaymentData(prev => ({ ...prev, reference_number: e.target.value }))}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="notes">Notes</Label>
                    <Textarea
                      id="notes"
                      placeholder="Additional payment notes..."
                      value={paymentData.notes}
                      onChange={(e) => setPaymentData(prev => ({ ...prev, notes: e.target.value }))}
                    />
                  </div>

                  <div className="pt-4">
                    <Button type="submit" disabled={saving} className="w-full sm:w-auto">
                      <Save className="mr-2 h-4 w-4" />
                      {saving ? 'Recording...' : 'Record Payment'}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </form>
          </div>

          {/* Payment Summary */}
          <div className="lg:col-span-1">
            {selectedInvoice && (
              <Card className="sticky top-6">
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <DollarSign className="mr-2 h-4 w-4" />
                    Invoice Summary
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Invoice:</span>
                      <span className="font-medium">{selectedInvoice.invoice_number}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Customer:</span>
                      <span className="font-medium">{selectedInvoice.customer?.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Total Amount:</span>
                      <span>{InvoiceService.formatCurrency(selectedInvoice.total_amount)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Paid Amount:</span>
                      <span>{InvoiceService.formatCurrency(selectedInvoice.paid_amount)}</span>
                    </div>
                    <hr />
                    <div className="flex justify-between font-bold text-lg">
                      <span>Outstanding:</span>
                      <span className="text-red-600">
                        {InvoiceService.formatCurrency(selectedInvoice.total_amount - selectedInvoice.paid_amount)}
                      </span>
                    </div>
                  </div>

                  {paymentData.amount > 0 && (
                    <>
                      <hr />
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Payment Amount:</span>
                          <span className="font-medium text-green-600">
                            {PaymentService.formatCurrency(paymentData.amount)}
                          </span>
                        </div>
                        <div className="flex justify-between font-bold">
                          <span>Remaining Balance:</span>
                          <span>
                            {InvoiceService.formatCurrency(
                              selectedInvoice.total_amount - selectedInvoice.paid_amount - paymentData.amount
                            )}
                          </span>
                        </div>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}