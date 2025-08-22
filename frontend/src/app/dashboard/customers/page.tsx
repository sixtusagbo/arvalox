'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Plus, Search, MoreHorizontal, Edit, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { CustomerService, Customer, CustomerCreate, CustomerUpdate, CustomerSearchParams } from '@/lib/customers';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function CustomersPage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deletingCustomer, setDeletingCustomer] = useState<Customer | null>(null);
  const { toast } = useToast();

  const [newCustomer, setNewCustomer] = useState<CustomerCreate>({
    customer_code: '',
    contact_name: '',
    email: '',
    phone: '',
    billing_address: '',
    shipping_address: '',
    credit_limit: 0,
    payment_terms: 30,
    tax_id: '',
    status: 'active',
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

  const loadCustomers = useCallback(async () => {
    try {
      setLoading(true);
      const params: CustomerSearchParams = {
        page,
        per_page: 20,
        search: searchTerm || undefined,
        status: statusFilter || undefined,
      };

      const response = await CustomerService.getCustomers(params);
      setCustomers(response.customers);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load customers',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [page, searchTerm, statusFilter, toast]);

  useEffect(() => {
    if (user) {
      loadCustomers();
    }
  }, [loadCustomers, user]);

  const handleCreateCustomer = async () => {
    try {
      await CustomerService.createCustomer(newCustomer);
      setIsCreateDialogOpen(false);
      setNewCustomer({
        customer_code: '',
        contact_name: '',
        email: '',
        phone: '',
        billing_address: '',
        shipping_address: '',
        credit_limit: 0,
        payment_terms: 30,
        tax_id: '',
        status: 'active',
      });
      toast({
        title: 'Success',
        description: 'Customer created successfully',
      });
      loadCustomers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create customer',
        variant: 'destructive',
      });
    }
  };

  const handleEditCustomer = async () => {
    if (!editingCustomer) return;

    try {
      const updateData: CustomerUpdate = {
        customer_code: editingCustomer.customer_code,
        contact_name: editingCustomer.contact_name,
        email: editingCustomer.email,
        phone: editingCustomer.phone,
        billing_address: editingCustomer.billing_address,
        shipping_address: editingCustomer.shipping_address,
        credit_limit: editingCustomer.credit_limit,
        payment_terms: editingCustomer.payment_terms,
        tax_id: editingCustomer.tax_id,
        status: editingCustomer.status,
      };

      await CustomerService.updateCustomer(editingCustomer.id, updateData);
      setIsEditDialogOpen(false);
      setEditingCustomer(null);
      toast({
        title: 'Success',
        description: 'Customer updated successfully',
      });
      loadCustomers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update customer',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteCustomer = async () => {
    if (!deletingCustomer) return;

    try {
      await CustomerService.deleteCustomer(deletingCustomer.id);
      setIsDeleteDialogOpen(false);
      setDeletingCustomer(null);
      toast({
        title: 'Success',
        description: 'Customer deleted successfully',
      });
      loadCustomers();
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to delete customer',
        variant: 'destructive',
      });
    }
  };

  const CustomerForm = ({ customer, onChange }: {
    customer: CustomerCreate | Customer;
    onChange: (field: string, value: string | number) => void;
  }) => (
    <div className="grid gap-4 py-4">
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="customer_code" className="text-right">
          Customer Code
        </Label>
        <Input
          id="customer_code"
          value={customer.customer_code}
          onChange={(e) => onChange('customer_code', e.target.value)}
          className="col-span-3"
          required
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="contact_name" className="text-right">
          Contact Name
        </Label>
        <Input
          id="contact_name"
          value={customer.contact_name || ''}
          onChange={(e) => onChange('contact_name', e.target.value)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="email" className="text-right">
          Email
        </Label>
        <Input
          id="email"
          type="email"
          value={customer.email || ''}
          onChange={(e) => onChange('email', e.target.value)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="phone" className="text-right">
          Phone
        </Label>
        <Input
          id="phone"
          value={customer.phone || ''}
          onChange={(e) => onChange('phone', e.target.value)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="billing_address" className="text-right">
          Billing Address
        </Label>
        <Textarea
          id="billing_address"
          value={customer.billing_address || ''}
          onChange={(e) => onChange('billing_address', e.target.value)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="shipping_address" className="text-right">
          Shipping Address
        </Label>
        <Textarea
          id="shipping_address"
          value={customer.shipping_address || ''}
          onChange={(e) => onChange('shipping_address', e.target.value)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="credit_limit" className="text-right">
          Credit Limit
        </Label>
        <Input
          id="credit_limit"
          type="number"
          min="0"
          step="0.01"
          value={customer.credit_limit}
          onChange={(e) => onChange('credit_limit', parseFloat(e.target.value) || 0)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="payment_terms" className="text-right">
          Payment Terms (days)
        </Label>
        <Input
          id="payment_terms"
          type="number"
          min="0"
          max="365"
          value={customer.payment_terms}
          onChange={(e) => onChange('payment_terms', parseInt(e.target.value) || 0)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="tax_id" className="text-right">
          Tax ID
        </Label>
        <Input
          id="tax_id"
          value={customer.tax_id || ''}
          onChange={(e) => onChange('tax_id', e.target.value)}
          className="col-span-3"
        />
      </div>
      <div className="grid grid-cols-4 items-center gap-4">
        <Label htmlFor="status" className="text-right">
          Status
        </Label>
        <Select
          value={customer.status}
          onValueChange={(value) => onChange('status', value)}
        >
          <SelectTrigger className="col-span-3">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );

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

  return (
    <DashboardLayout user={user}>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Customers</h2>
        <div className="flex items-center space-x-2">
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Customer
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[625px]">
              <DialogHeader>
                <DialogTitle>Create Customer</DialogTitle>
                <DialogDescription>
                  Add a new customer to your system.
                </DialogDescription>
              </DialogHeader>
              <CustomerForm
                customer={newCustomer}
                onChange={(field, value) => setNewCustomer(prev => ({ ...prev, [field]: value }))}
              />
              <DialogFooter>
                <Button onClick={handleCreateCustomer}>Create Customer</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search customers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select value={statusFilter || "all"} onValueChange={(value) => setStatusFilter(value === "all" ? "" : value)}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
            <SelectItem value="suspended">Suspended</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Customer List</CardTitle>
          <CardDescription>
            Manage your customers and their information.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-muted-foreground">Loading customers...</div>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer Code</TableHead>
                    <TableHead>Contact Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Phone</TableHead>
                    <TableHead>Credit Limit</TableHead>
                    <TableHead>Payment Terms</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {customers.map((customer) => (
                    <TableRow key={customer.id}>
                      <TableCell className="font-medium">{customer.customer_code}</TableCell>
                      <TableCell>{customer.contact_name || '-'}</TableCell>
                      <TableCell>{customer.email || '-'}</TableCell>
                      <TableCell>{customer.phone || '-'}</TableCell>
                      <TableCell>{CustomerService.formatCurrency(customer.credit_limit)}</TableCell>
                      <TableCell>{customer.payment_terms} days</TableCell>
                      <TableCell>
                        <Badge className={CustomerService.getStatusColor(customer.status)}>
                          {CustomerService.formatStatus(customer.status)}
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
                              onClick={() => {
                                setEditingCustomer(customer);
                                setIsEditDialogOpen(true);
                              }}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => {
                                setDeletingCustomer(customer);
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

              {customers.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No customers found.</p>
                </div>
              )}

              {totalPages > 1 && (
                <div className="flex items-center justify-between space-x-2 py-4">
                  <div className="text-sm text-muted-foreground">
                    Showing {customers.length} of {total} customers
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

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="sm:max-w-[625px]">
          <DialogHeader>
            <DialogTitle>Edit Customer</DialogTitle>
            <DialogDescription>
              Update customer information.
            </DialogDescription>
          </DialogHeader>
          {editingCustomer && (
            <CustomerForm
              customer={editingCustomer}
              onChange={(field, value) => setEditingCustomer(prev => prev ? { ...prev, [field]: value } : null)}
            />
          )}
          <DialogFooter>
            <Button onClick={handleEditCustomer}>Update Customer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Customer</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {deletingCustomer?.contact_name || deletingCustomer?.customer_code}? 
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteCustomer}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      </div>
    </DashboardLayout>
  );
}