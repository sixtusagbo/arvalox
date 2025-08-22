'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Users, 
  FileText, 
  AlertTriangle,
  Download,
  Calendar,
  Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { ReportsService, QuickStats, TopCustomer, RecentActivity, AgingMetrics, AgingAlerts } from '@/lib/reports';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function ReportsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [quickStats, setQuickStats] = useState<QuickStats | null>(null);
  const [topCustomers, setTopCustomers] = useState<TopCustomer[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [agingMetrics, setAgingMetrics] = useState<AgingMetrics | null>(null);
  const [agingAlerts, setAgingAlerts] = useState<AgingAlerts | null>(null);
  const [loading, setLoading] = useState(true);
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
      loadDashboardData();
    }
  }, [user]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load all dashboard data in parallel
      const [
        quickStatsData,
        topCustomersData,
        recentActivityData,
        agingMetricsData,
        agingAlertsData
      ] = await Promise.all([
        ReportsService.getQuickStats(),
        ReportsService.getTopCustomers(10),
        ReportsService.getRecentActivity(10),
        ReportsService.getAgingMetrics(),
        ReportsService.getAgingAlerts()
      ]);

      setQuickStats(quickStatsData);
      setTopCustomers(topCustomersData);
      setRecentActivity(recentActivityData);
      setAgingMetrics(agingMetricsData.metrics);
      setAgingAlerts(agingAlertsData.alerts);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExportAgingReport = async (format: 'csv' | 'pdf') => {
    try {
      const blob = await ReportsService.exportAgingReport(format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `aging-report.${format}`;
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
            <div className="text-muted-foreground">Loading reports...</div>
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
          <h2 className="text-3xl font-bold tracking-tight">Reports & Analytics</h2>
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={() => handleExportAgingReport('csv')}>
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
            <Button variant="outline" onClick={() => handleExportAgingReport('pdf')}>
              <Download className="mr-2 h-4 w-4" />
              Export PDF
            </Button>
            <Button onClick={() => router.push('/dashboard/reports/aging')}>
              <Eye className="mr-2 h-4 w-4" />
              View Aging Report
            </Button>
          </div>
        </div>

        {/* Alerts */}
        {agingAlerts && (agingAlerts.critical_overdue_count > 0 || agingAlerts.new_overdue_count > 0) && (
          <Card className="border-orange-200 bg-orange-50">
            <CardHeader>
              <CardTitle className="flex items-center text-orange-800">
                <AlertTriangle className="mr-2 h-4 w-4" />
                Collection Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {agingAlerts.critical_overdue_count > 0 && (
                  <div className="text-center">
                    <div className="text-2xl font-bold text-red-600">{agingAlerts.critical_overdue_count}</div>
                    <div className="text-sm text-muted-foreground">Critical Overdue (90+ days)</div>
                    <div className="text-xs text-red-600">
                      {ReportsService.formatCurrency(agingAlerts.critical_overdue_amount)}
                    </div>
                  </div>
                )}
                {agingAlerts.new_overdue_count > 0 && (
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{agingAlerts.new_overdue_count}</div>
                    <div className="text-sm text-muted-foreground">New Overdue</div>
                    <div className="text-xs text-orange-600">
                      {ReportsService.formatCurrency(agingAlerts.new_overdue_amount)}
                    </div>
                  </div>
                )}
                {agingAlerts.collection_risk_customers.length > 0 && (
                  <div className="text-center">
                    <div className="text-2xl font-bold text-yellow-600">{agingAlerts.collection_risk_customers.length}</div>
                    <div className="text-sm text-muted-foreground">At-Risk Customers</div>
                    <div className="text-xs text-yellow-600">
                      {ReportsService.formatCurrency(agingAlerts.total_at_risk_amount)}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Stats */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Revenue This Month</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {quickStats ? ReportsService.formatCurrency(quickStats.total_revenue_this_month) : '--'}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {quickStats ? ReportsService.formatCurrency(quickStats.total_outstanding) : '--'}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overdue</CardTitle>
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {quickStats ? ReportsService.formatCurrency(quickStats.overdue_amount) : '--'}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Customers</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {quickStats ? quickStats.total_customers : '--'}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Key Metrics */}
        {agingMetrics && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Collection Efficiency</CardTitle>
                <BarChart3 className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-green-600">
                  {ReportsService.formatPercentage(agingMetrics.collection_efficiency)}
                </div>
                <p className="text-xs text-muted-foreground">
                  Current vs Total Outstanding
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Days Outstanding</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {agingMetrics.average_days_outstanding.toFixed(1)}
                </div>
                <p className="text-xs text-muted-foreground">
                  Weighted by amount
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Overdue Rate</CardTitle>
                <TrendingDown className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-orange-600">
                  {ReportsService.formatPercentage(agingMetrics.overdue_percentage)}
                </div>
                <p className="text-xs text-muted-foreground">
                  Of total outstanding
                </p>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Worst Aging Customer</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-sm font-bold truncate">
                  {agingMetrics.worst_aging_customer || 'None'}
                </div>
                <p className="text-xs text-muted-foreground">
                  {ReportsService.formatCurrency(agingMetrics.worst_aging_amount)} overdue
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          {/* Top Customers */}
          <Card>
            <CardHeader>
              <CardTitle>Top Customers by Revenue</CardTitle>
              <CardDescription>Your highest value customers</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead className="text-right">Revenue</TableHead>
                    <TableHead className="text-right">Outstanding</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topCustomers.slice(0, 5).map((customer) => (
                    <TableRow key={customer.customer_id}>
                      <TableCell>
                        <div className="font-medium">{customer.customer_name}</div>
                        <div className="text-sm text-muted-foreground">
                          {customer.invoice_count} invoices
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {ReportsService.formatCurrency(customer.total_revenue)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span className={customer.outstanding_amount > 0 ? 'text-orange-600' : 'text-gray-500'}>
                          {ReportsService.formatCurrency(customer.outstanding_amount)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest invoices and payments</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity.slice(0, 8).map((activity) => (
                  <div key={`${activity.type}-${activity.id}`} className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {activity.type === 'invoice' ? (
                        <FileText className="h-4 w-4 text-blue-500" />
                      ) : (
                        <DollarSign className="h-4 w-4 text-green-500" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {activity.description}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {activity.customer_name} • {ReportsService.formatDate(activity.date)}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium">
                        {ReportsService.formatCurrency(activity.amount)}
                      </div>
                      <Badge variant={activity.status === 'paid' ? 'default' : 'secondary'} className="text-xs">
                        {activity.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="cursor-pointer hover:shadow-md transition-shadow" 
                onClick={() => router.push('/dashboard/reports/aging')}>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="mr-2 h-4 w-4" />
                Aging Report
              </CardTitle>
              <CardDescription>
                Detailed accounts receivable aging analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Report
              </Button>
            </CardContent>
          </Card>

          <Card className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => router.push('/dashboard/invoices')}>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="mr-2 h-4 w-4" />
                Invoice Management
              </CardTitle>
              <CardDescription>
                Manage and track all your invoices
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Invoices
              </Button>
            </CardContent>
          </Card>

          <Card className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => router.push('/dashboard/payments')}>
            <CardHeader>
              <CardTitle className="flex items-center">
                <DollarSign className="mr-2 h-4 w-4" />
                Payment Tracking
              </CardTitle>
              <CardDescription>
                Track and record customer payments
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" className="w-full">
                View Payments
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}