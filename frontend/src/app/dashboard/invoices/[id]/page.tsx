'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { ArrowLeft, Edit, Download, Send, Trash2, DollarSign } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
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

export default function InvoiceViewPage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const params = useParams();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const { toast } = useToast();

  const invoiceId = parseInt(params.id as string);

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
    const loadInvoice = async () => {
      if (!invoiceId || isNaN(invoiceId)) {
        router.push('/dashboard/invoices');
        return;
      }

      try {
        setLoading(true);
        const invoiceData = await InvoiceService.getInvoice(invoiceId);
        setInvoice(invoiceData);
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to load invoice',
          variant: 'destructive',
        });
        router.push('/dashboard/invoices');
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      loadInvoice();
    }
  }, [user, invoiceId, router, toast]);

  const handleDeleteInvoice = async () => {
    if (!invoice) return;

    try {
      await InvoiceService.deleteInvoice(invoice.id);
      setIsDeleteDialogOpen(false);
      toast({
        title: 'Success',
        description: 'Invoice deleted successfully',
      });
      router.push('/dashboard/invoices');
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete invoice',
        variant: 'destructive',
      });
    }
  };

  const handleDownloadPDF = async () => {
    if (!invoice) return;

    try {
      const blob = await InvoiceService.downloadInvoicePDF(invoice.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `invoice-${invoice.invoice_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to download invoice PDF',
        variant: 'destructive',
      });
    }
  };

  const handleSendEmail = async () => {
    if (!invoice) return;

    try {
      const result = await InvoiceService.sendInvoiceEmail(invoice.id);
      toast({
        title: 'Success',
        description: result.message,
      });
      
      // Refresh invoice data if status was updated
      if (result.status_updated) {
        const updatedInvoice = await InvoiceService.getInvoice(invoice.id);
        setInvoice(updatedInvoice);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to send invoice email',
        variant: 'destructive',
      });
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
            <div className="text-muted-foreground">Loading invoice...</div>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!invoice) {
    return (
      <DashboardLayout user={user}>
        <div className="flex-1 p-4 md:p-8 pt-6">
          <div className="text-center">
            <p className="text-muted-foreground">Invoice not found</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const balanceDue = invoice.total_amount - invoice.paid_amount;

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
              <h2 className="text-3xl font-bold tracking-tight">Invoice {invoice.invoice_number}</h2>
              <p className="text-muted-foreground">
                Created on {InvoiceService.formatDate(invoice.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={handleDownloadPDF}>
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
            {(invoice.status === 'draft' || invoice.status === 'sent') && (
              <Button onClick={() => router.push(`/dashboard/invoices/${invoice.id}/edit`)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
            {invoice.status === 'draft' && (
              <Button onClick={handleSendEmail}>
                <Send className="mr-2 h-4 w-4" />
                Send Invoice
              </Button>
            )}
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            {/* Invoice Details */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Invoice Details</CardTitle>
                    <CardDescription>Basic invoice information</CardDescription>
                  </div>
                  <Badge className={InvoiceService.getStatusColor(invoice.status)}>
                    {InvoiceService.formatStatus(invoice.status)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium text-sm text-muted-foreground">Bill To</h4>
                    <div className="mt-1">
                      <p className="font-medium">{invoice.customer?.name || 'Unknown Customer'}</p>
                      <p className="text-sm text-muted-foreground">{invoice.customer?.customer_code}</p>
                      {invoice.customer?.email && (
                        <p className="text-sm text-muted-foreground">{invoice.customer.email}</p>
                      )}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div>
                      <p className="text-sm text-muted-foreground">Invoice Date</p>
                      <p className="font-medium">{InvoiceService.formatDate(invoice.invoice_date)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">Due Date</p>
                      <p className="font-medium">{InvoiceService.formatDate(invoice.due_date)}</p>
                      {invoice.status === 'overdue' && (
                        <p className="text-sm text-red-600">
                          {InvoiceService.calculateDaysOverdue(invoice.due_date)} days overdue
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                {invoice.notes && (
                  <div className="mt-4">
                    <h4 className="font-medium text-sm text-muted-foreground">Notes</h4>
                    <p className="mt-1 text-sm">{invoice.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Invoice Items */}
            <Card>
              <CardHeader>
                <CardTitle>Invoice Items</CardTitle>
                <CardDescription>Items and services on this invoice</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-center">Quantity</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoice.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.description}</TableCell>
                        <TableCell className="text-center">{item.quantity}</TableCell>
                        <TableCell className="text-right">
                          {InvoiceService.formatCurrency(item.unit_price)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {InvoiceService.formatCurrency(item.total_amount)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                <div className="mt-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Subtotal:</span>
                    <span>{InvoiceService.formatCurrency(invoice.subtotal)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Tax:</span>
                    <span>{InvoiceService.formatCurrency(invoice.tax_amount)}</span>
                  </div>
                  <hr />
                  <div className="flex justify-between font-bold">
                    <span>Total:</span>
                    <span>{InvoiceService.formatCurrency(invoice.total_amount)}</span>
                  </div>
                  {invoice.paid_amount > 0 && (
                    <>
                      <div className="flex justify-between text-sm text-green-600">
                        <span>Paid:</span>
                        <span>-{InvoiceService.formatCurrency(invoice.paid_amount)}</span>
                      </div>
                      <div className="flex justify-between font-bold">
                        <span>Balance Due:</span>
                        <span className={balanceDue > 0 ? 'text-red-600' : 'text-green-600'}>
                          {InvoiceService.formatCurrency(balanceDue)}
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Actions & Summary */}
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
                    <span>Total Amount:</span>
                    <span className="font-medium">{InvoiceService.formatCurrency(invoice.total_amount)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Paid Amount:</span>
                    <span className="text-green-600 font-medium">
                      {InvoiceService.formatCurrency(invoice.paid_amount)}
                    </span>
                  </div>
                  <hr />
                  <div className="flex justify-between font-bold text-lg">
                    <span>Balance Due:</span>
                    <span className={balanceDue > 0 ? 'text-red-600' : 'text-green-600'}>
                      {InvoiceService.formatCurrency(balanceDue)}
                    </span>
                  </div>
                </div>

                {balanceDue > 0 && (
                  <Button className="w-full" onClick={() => router.push(`/dashboard/invoices/${invoice.id}/payment`)}>
                    Record Payment
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button variant="outline" className="w-full" onClick={handleDownloadPDF}>
                  <Download className="mr-2 h-4 w-4" />
                  Download PDF
                </Button>
                {(invoice.status === 'draft' || invoice.status === 'sent') && (
                  <Button variant="outline" className="w-full" onClick={() => router.push(`/dashboard/invoices/${invoice.id}/edit`)}>
                    <Edit className="mr-2 h-4 w-4" />
                    Edit Invoice
                  </Button>
                )}
                {invoice.status === 'draft' && (
                  <Button variant="outline" className="w-full" onClick={handleSendEmail}>
                    <Send className="mr-2 h-4 w-4" />
                    Send Invoice
                  </Button>
                )}
                <Button 
                  variant="outline" 
                  className="w-full text-red-600 border-red-200 hover:bg-red-50"
                  onClick={() => setIsDeleteDialogOpen(true)}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Invoice
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Delete Dialog */}
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Invoice</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete invoice {invoice.invoice_number}? 
                This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDeleteInvoice}>
                Delete
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}