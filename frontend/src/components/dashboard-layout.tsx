"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  LayoutDashboard,
  Users,
  FileText,
  CreditCard,
  BarChart3,
  Settings,
  LogOut,
  Bell,
  Plus,
} from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  organization_id: number;
  is_active: boolean;
  organization_name: string;
}

interface DashboardLayoutProps {
  children: ReactNode;
  user: User;
}

const navigationItems = [
  {
    title: "Overview",
    icon: LayoutDashboard,
    href: "/dashboard",
    isActive: true,
  },
  {
    title: "Customers",
    icon: Users,
    href: "/dashboard/customers",
  },
  {
    title: "Invoices",
    icon: FileText,
    href: "/dashboard/invoices",
  },
  {
    title: "Payments",
    icon: CreditCard,
    href: "/dashboard/payments",
  },
  {
    title: "Reports",
    icon: BarChart3,
    href: "/dashboard/reports",
  },
];

export function DashboardLayout({ children, user }: DashboardLayoutProps) {
  const router = useRouter();

  const handleLogout = async () => {
    const { AuthService } = await import("@/lib/auth");
    AuthService.logout();
    router.push("/");
  };

  const userInitials = `${user?.first_name?.[0] || ""}${
    user?.last_name?.[0] || ""
  }`;

  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full">
        <Sidebar className="border-r">
          <SidebarHeader className="border-b px-4 py-6">
            <div className="flex items-center space-x-2">
              <div className="text-xl font-bold text-blue-600">Arvalox</div>
            </div>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navigationItems.map((item) => (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton
                        asChild
                        isActive={item.isActive}
                        onClick={() => router.push(item.href)}>
                        <a href={item.href}>
                          <item.icon className="w-4 h-4" />
                          <span>{item.title}</span>
                        </a>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel>Quick Actions</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/dashboard/invoices/new">
                        <Plus className="w-4 h-4" />
                        <span>New Invoice</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild>
                      <a href="/dashboard/customers">
                        <Plus className="w-4 h-4" />
                        <span>Add Customer</span>
                      </a>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="border-t p-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="justify-start p-2 h-auto">
                  <Avatar className="w-8 h-8">
                    <AvatarImage
                      src=""
                      alt={`${user?.first_name} ${user?.last_name}`}
                    />
                    <AvatarFallback className="text-xs">
                      {userInitials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="ml-3 text-left">
                    <p className="text-sm font-medium">
                      {user?.first_name} {user?.last_name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-56" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {user?.first_name} {user?.last_name}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user?.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => router.push("/dashboard/settings")}>
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarFooter>
        </Sidebar>

        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="border-b bg-background">
            <div className="flex items-center justify-between px-6 py-3">
              <div className="flex items-center space-x-4">
                <SidebarTrigger />
                <h1 className="text-2xl font-semibold">
                  {user.organization_name || "Dashboard"}
                </h1>
              </div>
              <div className="flex items-center space-x-4">
                <ThemeToggle />
                <Button variant="ghost" size="sm">
                  <Bell className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1 p-6 bg-muted/30">{children}</main>
        </div>
      </div>
    </SidebarProvider>
  );
}
