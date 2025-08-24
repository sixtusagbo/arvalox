'use client';

import { useState, useEffect, useCallback, memo } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Search, MoreHorizontal, Edit, Trash2, Download, Send, Eye, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { LoadingState } from '@/components/ui/loading';
import { InvoiceService, Invoice, InvoiceSearchParams } from '@/lib/invoices';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function InvoicesPage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [dateFromFilter, setDateFromFilter] = useState('');
  const [dateToFilter, setDateToFilter] = useState('');
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deletingInvoice, setDeletingInvoice] = useState<Invoice | null>(null);
  const [sendingInvoices, setSendingInvoices] = useState<Set<number>>(new Set());
  const { toast } = useToast();

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

  const loadInvoices = useCallback(async () => {
    try {
      setLoading(true);
      const params: InvoiceSearchParams = {
        page,
        per_page: 20,
        search: searchTerm || undefined,
        status: statusFilter || undefined,
        date_from: dateFromFilter || undefined,
        date_to: dateToFilter || undefined,
      };

      const response = await InvoiceService.getInvoices(params);
      setInvoices(response.invoices);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load invoices',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, statusFilter, dateFromFilter, dateToFilter, toast]);

  useEffect(() => {
    if (user) {
      loadInvoices();
    }
  }, [loadInvoices, user]);

  const handleDeleteInvoice = async () => {
    if (!deletingInvoice) return;

    try {
      await InvoiceService.deleteInvoice(deletingInvoice.id);
      setIsDeleteDialogOpen(false);
      setDeletingInvoice(null);
      toast({
        title: 'Success',
        description: 'Invoice deleted successfully',
      });
      loadInvoices();
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete invoice',
        variant: 'destructive',
      });
    }
  };

  const handleDownloadPDF = async (invoiceId: number) => {
    try {
      const blob = await InvoiceService.downloadInvoicePDF(invoiceId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
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

  const handleSendInvoice = async (invoiceId: number) => {
    try {
      setSendingInvoices(prev => new Set(prev).add(invoiceId));
      const result = await InvoiceService.sendInvoiceEmail(invoiceId);
      
      toast({
        title: 'Success',
        description: result.message,
      });
      
      // Refresh the invoice list to get updated status
      if (result.status_updated) {
        loadInvoices();
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to send invoice email',
        variant: 'destructive',
      });
    } finally {
      setSendingInvoices(prev => {
        const newSet = new Set(prev);
        newSet.delete(invoiceId);
        return newSet;
      });
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setStatusFilter('');
    setDateFromFilter('');
    setDateToFilter('');
    setPage(1);
  };

  if (!user) {
    return <LoadingState />;
  }

  return (
    <DashboardLayout user={user}>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center justify-between space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Invoices</h2>
          <div className="flex items-center space-x-2">
            <Button 
              variant="outline" 
              onClick={() => router.push('/dashboard/invoices/overdue')}
            >
              <Clock className="mr-2 h-4 w-4" />
              Manage Overdue
            </Button>
            <Button onClick={() => router.push('/dashboard/invoices/new')}>
              <Plus className="mr-2 h-4 w-4" />
              Create Invoice
            </Button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search invoices..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8"
            />
          </div>
          <Select value={statusFilter || "all"} onValueChange={(value) => setStatusFilter(value === "all" ? "" : value)}>
            <SelectTrigger>
              <SelectValue placeholder="All Statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="sent">Sent</SelectItem>
              <SelectItem value="paid">Paid</SelectItem>
              <SelectItem value="overdue">Overdue</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
            </SelectContent>
          </Select>
          <Input
            type="date"
            placeholder="From Date"
            value={dateFromFilter}
            onChange={(e) => setDateFromFilter(e.target.value)}
          />
          <Input
            type="date"
            placeholder="To Date"
            value={dateToFilter}
            onChange={(e) => setDateToFilter(e.target.value)}
          />
          <Button variant="outline" onClick={clearFilters}>
            Clear Filters
          </Button>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Invoice List</CardTitle>
            <CardDescription>
              Manage your invoices and track payment status.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="text-muted-foreground">Loading invoices...</div>
              </div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Invoice #</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Due Date</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Paid</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {invoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="font-medium">{invoice.invoice_number}</TableCell>
                        <TableCell>
                          <div>
                            <div className="font-medium">{invoice.customer?.name || 'Unknown'}</div>
                            <div className="text-sm text-muted-foreground">{invoice.customer?.customer_code}</div>
                          </div>
                        </TableCell>
                        <TableCell>{InvoiceService.formatDate(invoice.invoice_date)}</TableCell>
                        <TableCell>
                          <div>
                            {InvoiceService.formatDate(invoice.due_date)}
                            {invoice.status === 'overdue' && (
                              <div className="text-xs text-red-600">
                                {InvoiceService.calculateDaysOverdue(invoice.due_date)} days overdue
                              </div>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{InvoiceService.formatCurrency(invoice.total_amount)}</TableCell>
                        <TableCell>{InvoiceService.formatCurrency(invoice.paid_amount)}</TableCell>
                        <TableCell>
                          <Badge className={InvoiceService.getStatusColor(invoice.status)}>
                            {InvoiceService.formatStatus(invoice.status)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <span className="sr-only">Open menu</span>
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuItem
                                onClick={() => router.push(`/dashboard/invoices/${invoice.id}`)}
                              >
                                <Eye className="mr-2 h-4 w-4" />
                                View
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => router.push(`/dashboard/invoices/${invoice.id}/edit`)}
                              >
                                <Edit className="mr-2 h-4 w-4" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleDownloadPDF(invoice.id)}
                              >
                                <Download className="mr-2 h-4 w-4" />
                                Download PDF
                              </DropdownMenuItem>
                              {invoice.status === 'draft' && (
                                <DropdownMenuItem
                                  onClick={() => handleSendInvoice(invoice.id)}
                                  disabled={sendingInvoices.has(invoice.id)}
                                >
                                  <Send className="mr-2 h-4 w-4" />
                                  {sendingInvoices.has(invoice.id) ? 'Sending...' : 'Send Invoice'}
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                onClick={() => {
                                  setDeletingInvoice(invoice);
                                  setIsDeleteDialogOpen(true);
                                }}
                                className="text-red-600"
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>

                {invoices.length === 0 && (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">No invoices found.</p>
                    <Button 
                      className="mt-4" 
                      onClick={() => router.push('/dashboard/invoices/new')}
                    >
                      Create your first invoice
                    </Button>
                  </div>
                )}

                {totalPages > 1 && (
                  <div className="flex items-center justify-between space-x-2 py-4">
                    <div className="text-sm text-muted-foreground">
                      Showing {invoices.length} of {total} invoices
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(page - 1)}
                        disabled={page <= 1}
                      >
                        Previous
                      </Button>
                      <div className="text-sm">
                        Page {page} of {totalPages}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(page + 1)}
                        disabled={page >= totalPages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Delete Dialog */}
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Invoice</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete invoice {deletingInvoice?.invoice_number}? 
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