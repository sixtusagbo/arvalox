"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  DollarSign,
  TrendingUp,
  TrendingDown,
  FileText,
  Users,
  Clock,
  AlertTriangle,
  Plus,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";
import { 
  DashboardService, 
  type DashboardMetrics, 
  type AgingReport, 
  type RecentActivity 
} from "@/lib/dashboard";

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [agingReport, setAgingReport] = useState<AgingReport | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [topCustomers, setTopCustomers] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const { AuthService } = await import("@/lib/auth");
        const token = AuthService.getToken();
        if (!token) {
          router.push("/login");
          return;
        }

        // Fetch user data
        const userData = await AuthService.getCurrentUser();
        if (!userData) {
          router.push("/login");
          return;
        }
        setUser(userData);

        // Fetch all dashboard data in parallel
        const [metricsData, agingData, activityData, customersData] = await Promise.all([
          DashboardService.getDashboardMetrics(),
          DashboardService.getAgingReport(),
          DashboardService.getRecentActivity(),
          DashboardService.getTopCustomers(),
        ]);

        setMetrics(metricsData);
        setAgingReport(agingData);
        setRecentActivity(activityData);
        setTopCustomers(customersData);

      } catch (error) {
        console.error("Error fetching dashboard data:", error);
        router.push("/login");
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardData();
  }, [router]);

  if (isLoading || !user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <DashboardLayout user={user}>
      <div className="space-y-6">
        {/* Welcome Section */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              Welcome back, {user.first_name}!
            </h2>
            <p className="text-muted-foreground">
              Here's what's happening with your accounts receivable today.
            </p>
          </div>
          <div className="flex space-x-2">
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              New Invoice
            </Button>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Outstanding</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {DashboardService.formatCurrency(metrics?.total_outstanding || 0)}
              </div>
              <p className="text-xs text-muted-foreground">
                <span className="inline-flex items-center text-green-600">
                  <TrendingUp className="w-3 h-3 mr-1" />
                  +8.2%
                </span>
                {" "}from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {DashboardService.formatCurrency(metrics?.monthly_revenue || 0)}
              </div>
              <p className="text-xs text-muted-foreground">
                <span className={`inline-flex items-center ${
                  (metrics?.revenue_growth_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(metrics?.revenue_growth_percentage || 0) >= 0 ? (
                    <ArrowUpRight className="w-3 h-3 mr-1" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3 mr-1" />
                  )}
                  {DashboardService.formatPercentage(metrics?.revenue_growth_percentage || 0)}
                </span>
                {" "}from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Invoices</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.active_invoices || 0}</div>
              <p className="text-xs text-muted-foreground">
                <span className={`inline-flex items-center ${
                  (metrics?.invoice_growth_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(metrics?.invoice_growth_percentage || 0) >= 0 ? (
                    <ArrowUpRight className="w-3 h-3 mr-1" />
                  ) : (
                    <ArrowDownRight className="w-3 h-3 mr-1" />
                  )}
                  {DashboardService.formatPercentage(metrics?.invoice_growth_percentage || 0)}
                </span>
                {" "}from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Collection Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics?.collection_rate || 0}%</div>
              <div className="mt-2">
                <Progress value={metrics?.collection_rate || 0} className="w-full" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="recent">Recent Activity</TabsTrigger>
            <TabsTrigger value="alerts">Alerts</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 lg:grid-cols-2">
              {/* Outstanding Invoices */}
              <Card>
                <CardHeader>
                  <CardTitle>Outstanding Invoices</CardTitle>
                  <CardDescription>
                    Invoices awaiting payment by age
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">0-30 days</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-green-500 h-2 rounded-full" 
                            style={{
                              width: `${agingReport?.total ? (agingReport.current / agingReport.total) * 100 : 0}%`
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">
                          {DashboardService.formatCurrency(agingReport?.current || 0)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">31-60 days</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-yellow-500 h-2 rounded-full" 
                            style={{
                              width: `${agingReport?.total ? (agingReport.thirty_days / agingReport.total) * 100 : 0}%`
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">
                          {DashboardService.formatCurrency(agingReport?.thirty_days || 0)}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">60+ days</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-red-500 h-2 rounded-full" 
                            style={{
                              width: `${agingReport?.total ? (agingReport.sixty_days / agingReport.total) * 100 : 0}%`
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium">
                          {DashboardService.formatCurrency(agingReport?.sixty_days || 0)}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Top Customers */}
              <Card>
                <CardHeader>
                  <CardTitle>Top Customers</CardTitle>
                  <CardDescription>
                    By outstanding balance
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {topCustomers.map((customer) => (
                      <div key={customer.id} className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{customer.name}</p>
                          <Badge variant={customer.status === "overdue" ? "destructive" : "secondary"}>
                            {customer.status}
                          </Badge>
                        </div>
                        <span className="font-medium">
                          {DashboardService.formatCurrency(customer.outstanding_balance)}
                        </span>
                      </div>
                    ))}
                    {topCustomers.length === 0 && (
                      <div className="text-center py-4 text-gray-500">
                        <p>No customers yet</p>
                        <p className="text-sm">Start by adding your first customer</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="recent" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>
                  Latest transactions and updates
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((activity) => (
                    <div key={activity.id} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium">{activity.description}</p>
                        {activity.customer_name && (
                          <p className="text-sm text-muted-foreground">
                            {activity.customer_name}
                            {activity.invoice_id && ` - Invoice #${activity.invoice_id}`}
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        {activity.amount && (
                          <p className={`font-medium ${
                            activity.type === 'payment_received' ? 'text-green-600' : ''
                          }`}>
                            {activity.type === 'payment_received' ? '+' : ''}
                            {DashboardService.formatCurrency(activity.amount)}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground">
                          {DashboardService.getTimeAgo(activity.created_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                  {recentActivity.length === 0 && (
                    <div className="text-center py-8 text-gray-500">
                      <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                      <p className="text-lg font-medium mb-2">No activity yet</p>
                      <p className="text-sm">
                        Once you start creating invoices and recording payments, you'll see your activity here.
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="alerts" className="space-y-4">
            <div className="grid gap-4">
              <Card className="border-yellow-200 bg-yellow-50">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-600" />
                    <CardTitle className="text-yellow-800">Payment Reminders</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-yellow-800 mb-3">
                    {Math.max(0, (metrics?.active_invoices || 0) - 5)} invoices are due for payment reminders
                  </p>
                  <Button variant="outline" size="sm">
                    Send Reminders
                  </Button>
                </CardContent>
              </Card>

              <Card className="border-red-200 bg-red-50">
                <CardHeader>
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-red-600" />
                    <CardTitle className="text-red-800">Overdue Invoices</CardTitle>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-red-800 mb-3">
                    {metrics?.overdue_invoices_count || 0} invoices are overdue totaling {DashboardService.formatCurrency(metrics?.total_overdue || 0)}
                  </p>
                  <Button variant="outline" size="sm">
                    View Overdue
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}