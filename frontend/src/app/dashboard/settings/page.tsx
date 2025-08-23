'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, Save, Eye, EyeOff, Building2, User, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { DashboardLayout } from '@/components/dashboard-layout';
import { LoadingState } from '@/components/ui/loading';
import { AuthService } from '@/lib/auth';

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

interface Organization {
  id: number;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
}

export default function SettingsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { toast } = useToast();

  // Profile form state
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
  });
  const [profileSaving, setProfileSaving] = useState(false);

  // Password form state
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [passwordSaving, setPasswordSaving] = useState(false);

  // Organization form state
  const [orgData, setOrgData] = useState({
    name: '',
    slug: '',
  });
  const [orgSaving, setOrgSaving] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        const token = AuthService.getToken();
        if (!token) {
          router.push('/login');
          return;
        }

        const [userData, orgData] = await Promise.all([
          AuthService.getCurrentUser(),
          AuthService.getOrganization(),
        ]);

        if (!userData) {
          router.push('/login');
          return;
        }

        setUser(userData);
        setOrganization(orgData);

        // Initialize form data
        setProfileData({
          first_name: userData.first_name,
          last_name: userData.last_name,
          email: userData.email,
        });

        setOrgData({
          name: orgData.name,
          slug: orgData.slug,
        });
      } catch (error) {
        console.error('Error loading data:', error);
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [router]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!profileData.first_name.trim() || !profileData.last_name.trim() || !profileData.email.trim()) {
      toast({
        title: 'Error',
        description: 'All fields are required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setProfileSaving(true);
      const updatedUser = await AuthService.updateProfile(profileData);
      setUser(updatedUser);
      toast({
        title: 'Success',
        description: 'Profile updated successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update profile',
        variant: 'destructive',
      });
    } finally {
      setProfileSaving(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!passwordData.current_password || !passwordData.new_password || !passwordData.confirm_password) {
      toast({
        title: 'Error',
        description: 'All password fields are required',
        variant: 'destructive',
      });
      return;
    }

    if (passwordData.new_password !== passwordData.confirm_password) {
      toast({
        title: 'Error',
        description: 'New passwords do not match',
        variant: 'destructive',
      });
      return;
    }

    if (passwordData.new_password.length < 8) {
      toast({
        title: 'Error',
        description: 'New password must be at least 8 characters long',
        variant: 'destructive',
      });
      return;
    }

    try {
      setPasswordSaving(true);
      await AuthService.changePassword({
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });

      // Clear form
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });

      toast({
        title: 'Success',
        description: 'Password changed successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to change password',
        variant: 'destructive',
      });
    } finally {
      setPasswordSaving(false);
    }
  };

  const handleOrganizationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!orgData.name.trim()) {
      toast({
        title: 'Error',
        description: 'Organization name is required',
        variant: 'destructive',
      });
      return;
    }

    try {
      setOrgSaving(true);
      const updatedOrg = await AuthService.updateOrganization(orgData);
      setOrganization(updatedOrg);
      toast({
        title: 'Success',
        description: 'Organization updated successfully',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to update organization',
        variant: 'destructive',
      });
    } finally {
      setOrgSaving(false);
    }
  };

  if (!user || loading) {
    return <LoadingState message="Loading settings..." />;
  }

  return (
    <DashboardLayout user={user}>
      <div className="flex-1 space-y-4 p-4 md:p-8 pt-6">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
          <h2 className="text-3xl font-bold tracking-tight">Settings</h2>
        </div>

        <Tabs defaultValue="profile" className="space-y-4">
          <TabsList>
            <TabsTrigger value="profile">
              <User className="mr-2 h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="password">
              <Lock className="mr-2 h-4 w-4" />
              Password
            </TabsTrigger>
            <TabsTrigger value="organization">
              <Building2 className="mr-2 h-4 w-4" />
              Organization
            </TabsTrigger>
          </TabsList>

          {/* Profile Tab */}
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Profile Information</CardTitle>
                <CardDescription>
                  Update your personal information and email address.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleProfileSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="first_name">First Name *</Label>
                      <Input
                        id="first_name"
                        value={profileData.first_name}
                        onChange={(e) => setProfileData(prev => ({ ...prev, first_name: e.target.value }))}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="last_name">Last Name *</Label>
                      <Input
                        id="last_name"
                        value={profileData.last_name}
                        onChange={(e) => setProfileData(prev => ({ ...prev, last_name: e.target.value }))}
                        required
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address *</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                      required
                    />
                  </div>

                  <Separator />
                  
                  <div className="pt-4">
                    <Button type="submit" disabled={profileSaving}>
                      <Save className="mr-2 h-4 w-4" />
                      {profileSaving ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Password Tab */}
          <TabsContent value="password">
            <Card>
              <CardHeader>
                <CardTitle>Change Password</CardTitle>
                <CardDescription>
                  Update your password to keep your account secure.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="current_password">Current Password *</Label>
                    <div className="relative">
                      <Input
                        id="current_password"
                        type={showPasswords.current ? 'text' : 'password'}
                        value={passwordData.current_password}
                        onChange={(e) => setPasswordData(prev => ({ ...prev, current_password: e.target.value }))}
                        required
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasswords(prev => ({ ...prev, current: !prev.current }))}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPasswords.current ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="new_password">New Password *</Label>
                    <div className="relative">
                      <Input
                        id="new_password"
                        type={showPasswords.new ? 'text' : 'password'}
                        value={passwordData.new_password}
                        onChange={(e) => setPasswordData(prev => ({ ...prev, new_password: e.target.value }))}
                        required
                        minLength={8}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasswords(prev => ({ ...prev, new: !prev.new }))}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPasswords.new ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm New Password *</Label>
                    <div className="relative">
                      <Input
                        id="confirm_password"
                        type={showPasswords.confirm ? 'text' : 'password'}
                        value={passwordData.confirm_password}
                        onChange={(e) => setPasswordData(prev => ({ ...prev, confirm_password: e.target.value }))}
                        required
                        minLength={8}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPasswords(prev => ({ ...prev, confirm: !prev.confirm }))}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showPasswords.confirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>

                  <Separator />
                  
                  <div className="pt-4">
                    <Button type="submit" disabled={passwordSaving}>
                      <Save className="mr-2 h-4 w-4" />
                      {passwordSaving ? 'Changing...' : 'Change Password'}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Organization Tab */}
          <TabsContent value="organization">
            <Card>
              <CardHeader>
                <CardTitle>Organization Settings</CardTitle>
                <CardDescription>
                  {user.role === 'owner' || user.role === 'admin' 
                    ? 'Manage your organization details and settings.'
                    : 'View your organization information. Only owners and admins can make changes.'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleOrganizationSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="org_name">Organization Name *</Label>
                    <Input
                      id="org_name"
                      value={orgData.name}
                      onChange={(e) => setOrgData(prev => ({ ...prev, name: e.target.value }))}
                      disabled={user.role !== 'owner' && user.role !== 'admin'}
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="org_slug">Organization Slug</Label>
                    <Input
                      id="org_slug"
                      value={orgData.slug}
                      onChange={(e) => setOrgData(prev => ({ ...prev, slug: e.target.value }))}
                      disabled={user.role !== 'owner' && user.role !== 'admin'}
                      placeholder="your-organization"
                    />
                    <p className="text-xs text-muted-foreground">
                      Used for custom URLs and integrations
                    </p>
                  </div>

                  {organization && (
                    <div className="space-y-2">
                      <Label>Created</Label>
                      <p className="text-sm text-muted-foreground">
                        {new Date(organization.created_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })}
                      </p>
                    </div>
                  )}

                  <Separator />
                  
                  {(user.role === 'owner' || user.role === 'admin') && (
                    <div className="pt-4">
                      <Button type="submit" disabled={orgSaving}>
                        <Save className="mr-2 h-4 w-4" />
                        {orgSaving ? 'Saving...' : 'Save Changes'}
                      </Button>
                    </div>
                  )}
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
}