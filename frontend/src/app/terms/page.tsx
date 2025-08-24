import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link href="/register">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Register
            </Button>
          </Link>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-3xl font-bold text-center">
              Terms of Service
            </CardTitle>
            <p className="text-center text-gray-600">
              Last updated:{" "}
              {new Date().toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </p>
          </CardHeader>

          <CardContent className="prose max-w-none">
            <div className="space-y-8">
              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  1. Acceptance of Terms
                </h2>
                <p className="text-gray-700 mb-4">
                  By accessing or using Arvalox ("the Service"), you agree to be
                  bound by these Terms of Service ("Terms"). If you disagree
                  with any part of these terms, then you may not access the
                  Service.
                </p>
                <p className="text-gray-700">
                  These Terms apply to all visitors, users, and others who
                  access or use the Service, including organizations and their
                  authorized users.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  2. Service Description
                </h2>
                <p className="text-gray-700 mb-4">
                  Arvalox is a Software-as-a-Service (SaaS) platform providing
                  accounts receivable management, invoicing, payment tracking,
                  customer relationship management, and financial reporting
                  tools for businesses.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  2.1 Core Features
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Customer and invoice management</li>
                  <li>Payment tracking and accounts receivable reports</li>
                  <li>Multi-user collaboration with role-based permissions</li>
                  <li>PDF invoice generation and email delivery</li>
                  <li>Financial analytics and aging reports</li>
                  <li>Multi-currency support and international formatting</li>
                  <li>Integration with payment processors (Paystack)</li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  2.2 Service Availability
                </h3>
                <p className="text-gray-700">
                  We strive to maintain 99.9% uptime but do not guarantee
                  uninterrupted service. Scheduled maintenance will be announced
                  in advance when possible.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  3. User Accounts and Registration
                </h2>

                <h3 className="text-xl font-semibold mb-3">
                  3.1 Account Creation
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    You must provide accurate and complete information during
                    registration
                  </li>
                  <li>
                    You are responsible for maintaining the security of your
                    account credentials
                  </li>
                  <li>
                    Each organization must have a unique account and cannot
                    share accounts
                  </li>
                  <li>
                    You must be at least 16 years old to create an account
                  </li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  3.2 User Roles and Responsibilities
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    <strong>Owner:</strong> Full access including subscription
                    management and user administration
                  </li>
                  <li>
                    <strong>Admin:</strong> Organization management and user
                    invitation capabilities
                  </li>
                  <li>
                    <strong>Accountant:</strong> Financial data access and
                    reporting capabilities
                  </li>
                  <li>
                    <strong>Sales Rep:</strong> Customer and invoice management
                    within assigned permissions
                  </li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  4. Subscription Plans and Billing
                </h2>

                <h3 className="text-xl font-semibold mb-3">
                  4.1 Subscription Tiers
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    <strong>Free Plan:</strong> Limited features with usage
                    restrictions
                  </li>
                  <li>
                    <strong>Starter Plan:</strong> Enhanced features for small
                    businesses
                  </li>
                  <li>
                    <strong>Professional Plan:</strong> Advanced features for
                    growing businesses
                  </li>
                  <li>
                    <strong>Enterprise Plan:</strong> Unlimited access for large
                    organizations
                  </li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  4.2 Billing Terms
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    Subscriptions are billed monthly or annually in advance
                  </li>
                  <li>All payments are processed securely through Paystack</li>
                  <li>Prices are subject to change with 30 days' notice</li>
                  <li>Failed payments may result in service suspension</li>
                  <li>
                    Downgrades take effect at the end of the current billing
                    period
                  </li>
                  <li>
                    Upgrades are effective immediately with prorated billing
                  </li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  4.3 Trial Periods
                </h3>
                <p className="text-gray-700">
                  Free trial periods are 14 days and do not require payment
                  information. Trial limitations apply and are clearly
                  communicated during signup.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  4.4 Refunds and Cancellations
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>You may cancel your subscription at any time</li>
                  <li>
                    Cancellations take effect at the end of the current billing
                    period
                  </li>
                  <li>
                    No refunds are provided for partial months unless required
                    by law
                  </li>
                  <li>
                    Data export options are available before account closure
                  </li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  5. Acceptable Use Policy
                </h2>

                <h3 className="text-xl font-semibold mb-3">
                  5.1 Permitted Uses
                </h3>
                <p className="text-gray-700 mb-4">
                  You may use Arvalox for legitimate business purposes
                  including:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    Managing customer relationships and accounts receivable
                  </li>
                  <li>Creating and sending professional invoices</li>
                  <li>Tracking payments and generating financial reports</li>
                  <li>Collaborating with team members on financial data</li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  5.2 Prohibited Uses
                </h3>
                <p className="text-gray-700 mb-4">
                  You may not use Arvalox to:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Violate any applicable laws or regulations</li>
                  <li>Infringe upon intellectual property rights</li>
                  <li>Transmit harmful, fraudulent, or deceptive content</li>
                  <li>Attempt to gain unauthorized access to systems</li>
                  <li>Interfere with or disrupt service operations</li>
                  <li>
                    Use the service for cryptocurrency or high-risk merchant
                    activities without prior approval
                  </li>
                  <li>
                    Resell or redistribute the service without authorization
                  </li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  6. Data Ownership and Security
                </h2>

                <h3 className="text-xl font-semibold mb-3">6.1 Your Data</h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    You retain ownership of all data you input into the Service
                  </li>
                  <li>
                    We implement industry-standard security measures to protect
                    your data
                  </li>
                  <li>
                    Data is isolated between organizations using multi-tenant
                    architecture
                  </li>
                  <li>
                    You can export your data at any time in standard formats
                  </li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  6.2 Data Processing
                </h3>
                <p className="text-gray-700 mb-4">
                  We process your data solely to provide the Service as
                  described in our Privacy Policy. You consent to such
                  processing and warrant that you have appropriate permissions
                  for any personal data you input.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  6.3 Backup and Recovery
                </h3>
                <p className="text-gray-700">
                  We maintain regular backups for disaster recovery purposes,
                  but recommend you maintain your own copies of critical data.
                  We are not liable for data loss except as required by law.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  7. Intellectual Property
                </h2>

                <h3 className="text-xl font-semibold mb-3">7.1 Our Rights</h3>
                <p className="text-gray-700 mb-4">
                  Arvalox and its associated trademarks, logos, and intellectual
                  property remain our exclusive property. You may not use our
                  branding without explicit written permission.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  7.2 License to Use
                </h3>
                <p className="text-gray-700 mb-4">
                  We grant you a limited, non-exclusive, non-transferable
                  license to use the Service during your subscription period,
                  subject to these Terms.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  7.3 Feedback and Suggestions
                </h3>
                <p className="text-gray-700">
                  Any feedback, suggestions, or improvements you provide become
                  our property and may be incorporated into the Service without
                  compensation.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  8. Third-Party Integrations
                </h2>
                <p className="text-gray-700 mb-4">
                  Our Service integrates with third-party providers including:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    <strong>Paystack:</strong> For payment processing and
                    subscription billing
                  </li>
                  <li>
                    <strong>Email Services:</strong> For automated notifications
                    and invoice delivery
                  </li>
                  <li>
                    <strong>Analytics Providers:</strong> For service
                    improvement and usage analysis
                  </li>
                </ul>
                <p className="text-gray-700">
                  Use of these services is subject to their respective terms and
                  privacy policies. We are not responsible for third-party
                  service interruptions or data handling practices.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  9. Limitation of Liability
                </h2>
                <p className="text-gray-700 mb-4">
                  TO THE MAXIMUM EXTENT PERMITTED BY LAW:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTIES OF ANY
                    KIND
                  </li>
                  <li>
                    WE ARE NOT LIABLE FOR INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
                    DAMAGES
                  </li>
                  <li>
                    OUR TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT PAID BY YOU
                    IN THE PRECEDING 12 MONTHS
                  </li>
                  <li>
                    WE ARE NOT LIABLE FOR DATA LOSS EXCEPT AS REQUIRED BY LAW
                  </li>
                  <li>
                    WE ARE NOT LIABLE FOR BUSINESS INTERRUPTION OR LOST PROFITS
                  </li>
                </ul>
                <p className="text-gray-700">
                  Some jurisdictions do not allow the exclusion of certain
                  warranties or liability, so the above limitations may not
                  apply to you.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  10. Indemnification
                </h2>
                <p className="text-gray-700">
                  You agree to indemnify and hold harmless Arvalox from any
                  claims, damages, or expenses arising from your use of the
                  Service, violation of these Terms, or infringement of any
                  third-party rights.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">11. Termination</h2>

                <h3 className="text-xl font-semibold mb-3">
                  11.1 Termination by You
                </h3>
                <p className="text-gray-700 mb-4">
                  You may terminate your account at any time. Upon termination,
                  your access to the Service will cease at the end of your
                  current billing period.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  11.2 Termination by Us
                </h3>
                <p className="text-gray-700 mb-4">
                  We may terminate or suspend your account immediately for:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Violation of these Terms</li>
                  <li>Non-payment of fees</li>
                  <li>Fraudulent or illegal activity</li>
                  <li>Prolonged inactivity (12+ months)</li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  11.3 Data Retention After Termination
                </h3>
                <p className="text-gray-700">
                  Following termination, we will retain your data for 30 days to
                  allow for reactivation. After this period, data may be
                  permanently deleted unless required for legal compliance.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  12. Dispute Resolution
                </h2>

                <h3 className="text-xl font-semibold mb-3">
                  12.1 Governing Law
                </h3>
                <p className="text-gray-700 mb-4">
                  These Terms are governed by and construed in accordance with
                  the laws of [Your Jurisdiction], without regard to conflict of
                  law provisions.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  12.2 Dispute Resolution Process
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>First, contact us directly to attempt resolution</li>
                  <li>
                    If unresolved, disputes may be subject to binding
                    arbitration
                  </li>
                  <li>
                    Small claims court remains available for qualifying disputes
                  </li>
                  <li>
                    Class action lawsuits are waived where legally permissible
                  </li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  13. Changes to Terms
                </h2>
                <p className="text-gray-700 mb-4">
                  We reserve the right to modify these Terms at any time. We
                  will notify users of material changes by:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Email notification to all registered users</li>
                  <li>Prominent notice within the application</li>
                  <li>Updated terms posted on our website</li>
                </ul>
                <p className="text-gray-700">
                  Continued use of the Service after changes constitutes
                  acceptance of the new Terms. Changes take effect 30 days after
                  notification unless immediate compliance is required by law.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  14. General Provisions
                </h2>

                <h3 className="text-xl font-semibold mb-3">
                  14.1 Entire Agreement
                </h3>
                <p className="text-gray-700 mb-4">
                  These Terms, together with our Privacy Policy, constitute the
                  entire agreement between you and Arvalox.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  14.2 Severability
                </h3>
                <p className="text-gray-700 mb-4">
                  If any provision of these Terms is found to be unenforceable,
                  the remaining provisions will remain in full force and effect.
                </p>

                <h3 className="text-xl font-semibold mb-3">14.3 Assignment</h3>
                <p className="text-gray-700 mb-4">
                  You may not assign your rights under these Terms without our
                  written consent. We may assign our rights and obligations to
                  any party.
                </p>

                <h3 className="text-xl font-semibold mb-3">
                  14.4 Force Majeure
                </h3>
                <p className="text-gray-700">
                  Neither party is liable for delays or failures in performance
                  due to circumstances beyond their reasonable control,
                  including natural disasters, government actions, or internet
                  disruptions.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  15. Contact Information
                </h2>
                <p className="text-gray-700 mb-4">
                  For questions about these Terms or our Service, please contact
                  us:
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700 mb-2">
                    <strong>Email:</strong> legal@arvalox.com
                  </p>
                  <p className="text-gray-700 mb-2">
                    <strong>Support:</strong> support@arvalox.com
                  </p>
                  <p className="text-gray-700 mb-2">
                    <strong>Business Inquiries:</strong> business@arvalox.com
                  </p>
                </div>
                <p className="text-gray-700 mt-4">
                  We will respond to inquiries within 5 business days.
                </p>
              </section>

              <div className="border-t pt-6 mt-8">
                <p className="text-sm text-gray-500 text-center">
                  These Terms of Service are effective as of{" "}
                  {new Date().toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}{" "}
                  and apply to all users of the Arvalox platform.
                </p>
                <p className="text-sm text-gray-500 text-center mt-2">
                  By using Arvalox, you acknowledge that you have read,
                  understood, and agree to be bound by these Terms of Service.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
