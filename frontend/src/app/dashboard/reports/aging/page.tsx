'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Download, Filter, Calendar, BarChart3, TrendingUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { LoadingState } from '@/components/ui/loading';
import { ReportsService, AgingReport, CustomerAgingSummary } from '@/lib/reports';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function AgingReportPage() {
  const [user, setUser] = useState<User | null>(null);
  const [agingReport, setAgingReport] = useState<AgingReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  const [includePaid, setIncludePaid] = useState(false);
  const [viewMode, setViewMode] = useState<'summary' | 'customers' | 'invoices'>('summary');
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
      loadAgingReport();
    }
  }, [user, asOfDate, includePaid]);

  const loadAgingReport = async () => {
    try {
      setLoading(true);
      const report = await ReportsService.getAgingReport(asOfDate, undefined, includePaid);
      setAgingReport(report);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load aging report',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'pdf') => {
    try {
      const blob = await ReportsService.exportAgingReport(format, {
        asOfDate,
        includePaid
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `aging-report-${asOfDate}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({
        title: 'Success',
        description: `Aging report exported as ${format.toUpperCase()}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to export aging report',
        variant: 'destructive',
      });
    }
  };

  if (!user) {
    return <LoadingState message="Loading aging report..." />;
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
              <h2 className="text-3xl font-bold tracking-tight">Accounts Receivable Aging Report</h2>
              <p className="text-muted-foreground">
                As of {ReportsService.formatDate(asOfDate)}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={() => handleExport('csv')}>
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
            <Button variant="outline" onClick={() => handleExport('pdf')}>
              <Download className="mr-2 h-4 w-4" />
              Export PDF
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Filter className="mr-2 h-4 w-4" />
              Report Filters
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="asOfDate">As of Date</Label>
                <Input
                  id="asOfDate"
                  type="date"
                  value={asOfDate}
                  onChange={(e) => setAsOfDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="includePaid">Include Paid</Label>
                <Select 
                  value={includePaid.toString()} 
                  onValueChange={(value) => setIncludePaid(value === 'true')}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="false">Outstanding Only</SelectItem>
                    <SelectItem value="true">Include Paid Invoices</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="viewMode">View Mode</Label>
                <Select value={viewMode} onValueChange={(value: any) => setViewMode(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="summary">Summary</SelectItem>
                    <SelectItem value="customers">By Customer</SelectItem>
                    <SelectItem value="invoices">Invoice Details</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="text-muted-foreground">Loading aging report...</div>
          </div>
        ) : agingReport ? (
          <>
            {/* Summary Cards */}
            <div className="grid gap-4 md:grid-cols-5">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Current</CardTitle>
                  <div className="text-xs text-green-600">0 days</div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-green-600">
                    {ReportsService.formatCurrency(agingReport.summary.current.amount)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {agingReport.summary.current.count} invoices
                  </p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">1-30 Days</CardTitle>
                  <div className="text-xs text-yellow-600">Past due</div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-yellow-600">
                    {ReportsService.formatCurrency(agingReport.summary.days_1_30.amount)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {agingReport.summary.days_1_30.count} invoices
                  </p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">31-60 Days</CardTitle>
                  <div className="text-xs text-orange-600">Overdue</div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-orange-600">
                    {ReportsService.formatCurrency(agingReport.summary.days_31_60.amount)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {agingReport.summary.days_31_60.count} invoices
                  </p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">61-90 Days</CardTitle>
                  <div className="text-xs text-red-600">High risk</div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-600">
                    {ReportsService.formatCurrency(agingReport.summary.days_61_90.amount)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {agingReport.summary.days_61_90.count} invoices
                  </p>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">90+ Days</CardTitle>
                  <div className="text-xs text-red-800">Critical</div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold text-red-800">
                    {ReportsService.formatCurrency(agingReport.summary.days_over_90.amount)}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {agingReport.summary.days_over_90.count} invoices
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Total Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Total Outstanding
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-4xl font-bold text-blue-600 mb-2">
                  {ReportsService.formatCurrency(agingReport.summary.total.amount)}
                </div>
                <div className="text-lg text-muted-foreground">
                  Across {agingReport.summary.total.count} invoices
                </div>
                
                {/* Percentage breakdown */}
                <div className="mt-4 grid grid-cols-5 gap-2 text-sm">
                  <div className="text-center">
                    <div className="font-medium text-green-600">
                      {((agingReport.summary.current.amount / agingReport.summary.total.amount) * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">Current</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-yellow-600">
                      {((agingReport.summary.days_1_30.amount / agingReport.summary.total.amount) * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">1-30</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-orange-600">
                      {((agingReport.summary.days_31_60.amount / agingReport.summary.total.amount) * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">31-60</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-red-600">
                      {((agingReport.summary.days_61_90.amount / agingReport.summary.total.amount) * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">61-90</div>
                  </div>
                  <div className="text-center">
                    <div className="font-medium text-red-800">
                      {((agingReport.summary.days_over_90.amount / agingReport.summary.total.amount) * 100).toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">90+</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detail Tables */}
            {viewMode === 'customers' && (
              <Card>
                <CardHeader>
                  <CardTitle>Aging by Customer</CardTitle>
                  <CardDescription>Outstanding amounts grouped by customer</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Customer</TableHead>
                        <TableHead className="text-right">Current</TableHead>
                        <TableHead className="text-right">1-30 Days</TableHead>
                        <TableHead className="text-right">31-60 Days</TableHead>
                        <TableHead className="text-right">61-90 Days</TableHead>
                        <TableHead className="text-right">90+ Days</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {agingReport.customer_summaries.map((customer: CustomerAgingSummary) => (
                        <TableRow key={customer.customer_id}>
                          <TableCell>
                            <div className="font-medium">{customer.customer_name}</div>
                            <div className="text-sm text-muted-foreground">{customer.customer_code}</div>
                          </TableCell>
                          <TableCell className="text-right text-green-600">
                            {ReportsService.formatCurrency(customer.current)}
                          </TableCell>
                          <TableCell className="text-right text-yellow-600">
                            {ReportsService.formatCurrency(customer.days_1_30)}
                          </TableCell>
                          <TableCell className="text-right text-orange-600">
                            {ReportsService.formatCurrency(customer.days_31_60)}
                          </TableCell>
                          <TableCell className="text-right text-red-600">
                            {ReportsService.formatCurrency(customer.days_61_90)}
                          </TableCell>
                          <TableCell className="text-right text-red-800">
                            {ReportsService.formatCurrency(customer.days_over_90)}
                          </TableCell>
                          <TableCell className="text-right font-bold">
                            {ReportsService.formatCurrency(customer.total)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}

            {viewMode === 'invoices' && (
              <Card>
                <CardHeader>
                  <CardTitle>Invoice Details</CardTitle>
                  <CardDescription>Detailed breakdown by individual invoices</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Invoice</TableHead>
                        <TableHead>Customer</TableHead>
                        <TableHead>Invoice Date</TableHead>
                        <TableHead>Due Date</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead className="text-right">Outstanding</TableHead>
                        <TableHead className="text-right">Days Overdue</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {agingReport.invoice_details.map((invoice) => (
                        <TableRow key={invoice.invoice_id}>
                          <TableCell>
                            <div className="font-medium">{invoice.invoice_number}</div>
                          </TableCell>
                          <TableCell>{invoice.customer_name}</TableCell>
                          <TableCell>{ReportsService.formatDate(invoice.invoice_date)}</TableCell>
                          <TableCell>{ReportsService.formatDate(invoice.due_date)}</TableCell>
                          <TableCell className="text-right">
                            {ReportsService.formatCurrency(invoice.total_amount)}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            <span className={ReportsService.getAgingBucketColor(invoice.aging_bucket)}>
                              {ReportsService.formatCurrency(invoice.outstanding_amount)}
                            </span>
                          </TableCell>
                          <TableCell className="text-right">
                            <span className={invoice.days_overdue > 0 ? 'text-red-600' : 'text-green-600'}>
                              {invoice.days_overdue > 0 ? `${invoice.days_overdue} days` : 'Current'}
                            </span>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}
          </>
        ) : (
          <div className="text-center py-8">
            <p className="text-muted-foreground">No aging data available</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}