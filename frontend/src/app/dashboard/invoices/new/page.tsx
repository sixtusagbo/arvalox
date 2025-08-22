'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Plus, Trash2, Calculator } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { InvoiceService, InvoiceCreate, InvoiceItem } from '@/lib/invoices';
import { CustomerService, Customer } from '@/lib/customers';

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
}

export default function NewInvoicePage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(false);
  const [taxRate, setTaxRate] = useState(0);
  const { toast } = useToast();

  const [invoiceData, setInvoiceData] = useState({
    customer_id: 0,
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days from now
    notes: '',
    status: 'draft' as const,
  });

  const [items, setItems] = useState<Omit<InvoiceItem, 'id'>[]>([
    { description: '', quantity: 1, unit_price: 0, total_amount: 0 }
  ]);

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
    const loadCustomers = async () => {
      try {
        const response = await CustomerService.getCustomers({ per_page: 100 });
        setCustomers(response.customers);
      } catch (error) {
        console.error('Error loading customers:', error);
      }
    };

    if (user) {
      loadCustomers();
    }
  }, [user]);

  const updateItemQuantity = useCallback((index: number, quantity: number) => {
    setItems(prev => prev.map((item, i) => {
      if (i === index) {
        const total_amount = InvoiceService.calculateItemTotal(quantity, item.unit_price);
        return { ...item, quantity, total_amount };
      }
      return item;
    }));
  }, []);

  const updateItemPrice = useCallback((index: number, unit_price: number) => {
    setItems(prev => prev.map((item, i) => {
      if (i === index) {
        const total_amount = InvoiceService.calculateItemTotal(item.quantity, unit_price);
        return { ...item, unit_price, total_amount };
      }
      return item;
    }));
  }, []);

  const updateItemDescription = useCallback((index: number, description: string) => {
    setItems(prev => prev.map((item, i) => 
      i === index ? { ...item, description } : item
    ));
  }, []);

  const addItem = () => {
    setItems(prev => [...prev, { description: '', quantity: 1, unit_price: 0, total_amount: 0 }]);
  };

  const removeItem = (index: number) => {
    if (items.length > 1) {
      setItems(prev => prev.filter((_, i) => i !== index));
    }
  };

  const subtotal = InvoiceService.calculateSubtotal(items);
  const taxAmount = InvoiceService.calculateTax(subtotal, taxRate);
  const total = InvoiceService.calculateTotal(subtotal, taxAmount);

  const handleSubmit = async (status: 'draft' | 'sent') => {
    if (!invoiceData.customer_id) {
      toast({
        title: 'Error',
        description: 'Please select a customer',
        variant: 'destructive',
      });
      return;
    }

    if (items.some(item => !item.description.trim())) {
      toast({
        title: 'Error',
        description: 'Please fill in all item descriptions',
        variant: 'destructive',
      });
      return;
    }

    try {
      setLoading(true);

      const invoiceCreateData: InvoiceCreate = {
        ...invoiceData,
        customer_id: invoiceData.customer_id,
        subtotal,
        tax_amount: taxAmount,
        total_amount: total,
        status,
        items,
      };

      const newInvoice = await InvoiceService.createInvoice(invoiceCreateData);
      
      toast({
        title: 'Success',
        description: `Invoice ${status === 'draft' ? 'saved as draft' : 'created and sent'} successfully`,
      });

      router.push(`/dashboard/invoices/${newInvoice.id}`);
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create invoice',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
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

  return (
    <DashboardLayout user={user}>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h2 className="text-3xl font-bold tracking-tight">Create New Invoice</h2>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            {/* Invoice Details */}
            <Card>
              <CardHeader>
                <CardTitle>Invoice Details</CardTitle>
                <CardDescription>Basic information about the invoice</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="customer">Customer *</Label>
                    <Select
                      value={invoiceData.customer_id.toString()}
                      onValueChange={(value) => setInvoiceData(prev => ({ ...prev, customer_id: parseInt(value) }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select customer" />
                      </SelectTrigger>
                      <SelectContent>
                        {customers.map((customer) => (
                          <SelectItem key={customer.id} value={customer.id.toString()}>
                            {customer.name} ({customer.customer_code})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="invoice_date">Invoice Date *</Label>
                    <Input
                      id="invoice_date"
                      type="date"
                      value={invoiceData.invoice_date}
                      onChange={(e) => setInvoiceData(prev => ({ ...prev, invoice_date: e.target.value }))}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="due_date">Due Date *</Label>
                    <Input
                      id="due_date"
                      type="date"
                      value={invoiceData.due_date}
                      onChange={(e) => setInvoiceData(prev => ({ ...prev, due_date: e.target.value }))}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tax_rate">Tax Rate (%)</Label>
                    <Input
                      id="tax_rate"
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={taxRate}
                      onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="notes">Notes</Label>
                  <Textarea
                    id="notes"
                    placeholder="Additional notes or terms..."
                    value={invoiceData.notes}
                    onChange={(e) => setInvoiceData(prev => ({ ...prev, notes: e.target.value }))}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Invoice Items */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Invoice Items</CardTitle>
                    <CardDescription>Add items and services to the invoice</CardDescription>
                  </div>
                  <Button onClick={addItem}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Item
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Description</TableHead>
                      <TableHead className="w-24">Qty</TableHead>
                      <TableHead className="w-32">Unit Price</TableHead>
                      <TableHead className="w-32">Total</TableHead>
                      <TableHead className="w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Input
                            placeholder="Item description"
                            value={item.description}
                            onChange={(e) => updateItemDescription(index, e.target.value)}
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            value={item.quantity}
                            onChange={(e) => updateItemQuantity(index, parseFloat(e.target.value) || 0)}
                          />
                        </TableCell>
                        <TableCell>
                          <Input
                            type="number"
                            min="0"
                            step="0.01"
                            value={item.unit_price}
                            onChange={(e) => updateItemPrice(index, parseFloat(e.target.value) || 0)}
                          />
                        </TableCell>
                        <TableCell>
                          <div className="font-medium">
                            {InvoiceService.formatCurrency(item.total_amount)}
                          </div>
                        </TableCell>
                        <TableCell>
                          {items.length > 1 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => removeItem(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>

          {/* Invoice Summary */}
          <div className="lg:col-span-1">
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Calculator className="mr-2 h-4 w-4" />
                  Invoice Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Subtotal:</span>
                    <span>{InvoiceService.formatCurrency(subtotal)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Tax ({taxRate}%):</span>
                    <span>{InvoiceService.formatCurrency(taxAmount)}</span>
                  </div>
                  <hr />
                  <div className="flex justify-between font-bold text-lg">
                    <span>Total:</span>
                    <span>{InvoiceService.formatCurrency(total)}</span>
                  </div>
                </div>

                <div className="space-y-2 pt-4">
                  <Button
                    className="w-full"
                    onClick={() => handleSubmit('sent')}
                    disabled={loading}
                  >
                    Create & Send Invoice
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleSubmit('draft')}
                    disabled={loading}
                  >
                    Save as Draft
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}