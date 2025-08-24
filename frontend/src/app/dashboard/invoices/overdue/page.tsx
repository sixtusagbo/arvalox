'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Send, Clock, AlertTriangle, CheckCircle, Mail } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { LoadingState } from '@/components/ui/loading';
import { ReportsService, AgingInvoiceDetail } from '@/lib/reports';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function OverdueInvoicesPage() {
  const [user, setUser] = useState<User | null>(null);
  const [overdueInvoices, setOverdueInvoices] = useState<AgingInvoiceDetail[]>([]);
  const [selectedInvoices, setSelectedInvoices] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [daysFilter, setDaysFilter] = useState(1);
  const router = useRouter();
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

  useEffect(() => {
    if (user) {
      loadOverdueInvoices();
    }
  }, [user, daysFilter]);

  const loadOverdueInvoices = async () => {
    try {
      setLoading(true);
      const invoices = await ReportsService.getOverdueInvoices(daysFilter);
      setOverdueInvoices(invoices);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load overdue invoices',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedInvoices(new Set(overdueInvoices.map(invoice => invoice.invoice_id)));
    } else {
      setSelectedInvoices(new Set());
    }
  };

  const handleSelectInvoice = (invoiceId: number, checked: boolean) => {
    const newSelected = new Set(selectedInvoices);
    if (checked) {
      newSelected.add(invoiceId);
    } else {
      newSelected.delete(invoiceId);
    }
    setSelectedInvoices(newSelected);
  };

  const handleSendReminders = async () => {
    if (selectedInvoices.size === 0) {
      toast({
        title: 'No Selection',
        description: 'Please select at least one invoice to send reminders',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSending(true);
      const invoiceIds = Array.from(selectedInvoices);
      const result = await ReportsService.sendBulkReminders(invoiceIds);

      if (result.successful > 0) {
        toast({
          title: 'Reminders Sent',
          description: `${result.successful} reminder(s) sent successfully${result.failed > 0 ? `, ${result.failed} failed` : ''}`,
        });
      }

      if (result.failed > 0 && result.successful === 0) {
        toast({
          title: 'Failed to Send',
          description: `Failed to send ${result.failed} reminder(s). Please check customer email addresses.`,
          variant: 'destructive',
        });
      }

      // Clear selection and reload
      setSelectedInvoices(new Set());
      await loadOverdueInvoices();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to send reminders',
        variant: 'destructive',
      });
    } finally {
      setSending(false);
    }
  };

  const getOverdueSeverity = (daysOverdue: number) => {
    if (daysOverdue >= 90) return { color: 'text-red-800', bg: 'bg-red-100', label: 'Critical' };
    if (daysOverdue >= 60) return { color: 'text-red-600', bg: 'bg-red-50', label: 'High Risk' };
    if (daysOverdue >= 30) return { color: 'text-orange-600', bg: 'bg-orange-50', label: 'Overdue' };
    return { color: 'text-yellow-600', bg: 'bg-yellow-50', label: 'Past Due' };
  };

  if (!user) {
    return <LoadingState />;
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
              <h2 className="text-3xl font-bold tracking-tight">Overdue Invoices</h2>
              <p className="text-muted-foreground">
                Invoices that are past their due date
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <select
              className="px-3 py-2 border rounded-md"
              value={daysFilter}
              onChange={(e) => setDaysFilter(parseInt(e.target.value))}
            >
              <option value={1}>1+ days overdue</option>
              <option value={7}>7+ days overdue</option>
              <option value={30}>30+ days overdue</option>
              <option value={60}>60+ days overdue</option>
              <option value={90}>90+ days overdue</option>
            </select>
            {selectedInvoices.size > 0 && (
              <Button onClick={handleSendReminders} disabled={sending}>
                <Send className="mr-2 h-4 w-4" />
                {sending ? 'Sending...' : `Send Reminders (${selectedInvoices.size})`}
              </Button>
            )}
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Overdue</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overdueInvoices.length}</div>
              <p className="text-xs text-muted-foreground">invoices</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Amount</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {ReportsService.formatCurrency(
                  overdueInvoices.reduce((sum, invoice) => sum + Number(invoice.outstanding_amount || 0), 0)
                )}
              </div>
              <p className="text-xs text-muted-foreground">outstanding</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Days Overdue</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {overdueInvoices.length > 0 
                  ? Math.round(overdueInvoices.reduce((sum, invoice) => sum + Number(invoice.days_overdue || 0), 0) / overdueInvoices.length)
                  : 0
                } days
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Selected</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{selectedInvoices.size}</div>
              <p className="text-xs text-muted-foreground">for reminders</p>
            </CardContent>
          </Card>
        </div>

        {/* Overdue Invoices Table */}
        <Card>
          <CardHeader>
            <CardTitle>Overdue Invoice Details</CardTitle>
            <CardDescription>
              Select invoices to send payment reminders
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="text-muted-foreground">Loading overdue invoices...</div>
              </div>
            ) : overdueInvoices.length > 0 ? (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">
                      <Checkbox
                        checked={selectedInvoices.size === overdueInvoices.length && overdueInvoices.length > 0}
                        onCheckedChange={handleSelectAll}
                      />
                    </TableHead>
                    <TableHead>Invoice</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead className="text-right">Outstanding</TableHead>
                    <TableHead className="text-center">Days Overdue</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {overdueInvoices.map((invoice) => {
                    const severity = getOverdueSeverity(invoice.days_overdue);
                    return (
                      <TableRow key={invoice.invoice_id}>
                        <TableCell>
                          <Checkbox
                            checked={selectedInvoices.has(invoice.invoice_id)}
                            onCheckedChange={(checked) => 
                              handleSelectInvoice(invoice.invoice_id, !!checked)
                            }
                          />
                        </TableCell>
                        <TableCell>
                          <div className="font-medium">{invoice.invoice_number}</div>
                        </TableCell>
                        <TableCell>
                          <div className="font-medium">{invoice.customer_name}</div>
                        </TableCell>
                        <TableCell>
                          <div className="text-red-600">
                            {ReportsService.formatDate(invoice.due_date)}
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          {ReportsService.formatCurrency(invoice.total_amount)}
                        </TableCell>
                        <TableCell className="text-right font-medium text-red-600">
                          {ReportsService.formatCurrency(invoice.outstanding_amount)}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline" className={`${severity.color} ${severity.bg}`}>
                            {invoice.days_overdue} days
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="outline" className={`${severity.color} ${severity.bg}`}>
                            {severity.label}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            ) : (
              <div className="text-center py-8">
                <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                <h3 className="text-lg font-medium mb-2">No Overdue Invoices</h3>
                <p className="text-muted-foreground">
                  Great! All invoices are current or have been paid.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}