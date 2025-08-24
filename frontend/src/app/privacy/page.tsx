import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function PrivacyPolicyPage() {
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
              Privacy Policy
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
                <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
                <p className="text-gray-700 mb-4">
                  Welcome to Arvalox ("we," "our," or "us"). This Privacy Policy
                  explains how we collect, use, disclose, and safeguard your
                  information when you use our accounts receivable management
                  platform and related services (collectively, the "Service").
                </p>
                <p className="text-gray-700">
                  We respect your privacy and are committed to protecting your
                  personal data. This privacy policy will inform you about how
                  we look after your personal data and tell you about your
                  privacy rights and how the law protects you.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  2. Information We Collect
                </h2>

                <h3 className="text-xl font-semibold mb-3">
                  2.1 Personal Information
                </h3>
                <p className="text-gray-700 mb-4">
                  We collect the following personal information:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    <strong>Account Information:</strong> Name, email address,
                    password, and user role
                  </li>
                  <li>
                    <strong>Organization Information:</strong> Business name,
                    address, phone number, tax information
                  </li>
                  <li>
                    <strong>Financial Information:</strong> Subscription and
                    billing information (processed by Paystack)
                  </li>
                  <li>
                    <strong>Customer Data:</strong> Customer names, contact
                    details, billing addresses, and payment information you
                    input
                  </li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  2.2 Business Data
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Invoice details, amounts, and payment records</li>
                  <li>Transaction histories and financial calculations</li>
                  <li>Customer payment terms and credit limits</li>
                  <li>Usage analytics and feature utilization data</li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  2.3 Technical Data
                </h3>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Login timestamps and activity logs</li>
                  <li>Device information and IP addresses</li>
                  <li>Browser type and version</li>
                  <li>Usage patterns and feature interactions</li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  3. How We Use Your Information
                </h2>
                <p className="text-gray-700 mb-4">
                  We use your information to:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    Provide and maintain our accounts receivable management
                    services
                  </li>
                  <li>Process payments and manage your subscription</li>
                  <li>Generate invoices and financial reports</li>
                  <li>
                    Send automated emails including invoices and payment
                    reminders
                  </li>
                  <li>
                    Provide customer support and respond to your inquiries
                  </li>
                  <li>Monitor usage and enforce subscription limits</li>
                  <li>Improve our services and develop new features</li>
                  <li>Comply with legal obligations and prevent fraud</li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  4. Information Sharing and Disclosure
                </h2>

                <h3 className="text-xl font-semibold mb-3">
                  4.1 Third-Party Service Providers
                </h3>
                <p className="text-gray-700 mb-4">
                  We share your information with trusted third parties who help
                  us operate our service:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    <strong>Paystack:</strong> Payment processing for
                    subscriptions and transactions
                  </li>
                  <li>
                    <strong>Email Service Providers:</strong> For sending
                    transactional emails and notifications
                  </li>
                  <li>
                    <strong>Cloud Infrastructure Providers:</strong> For hosting
                    and data storage
                  </li>
                  <li>
                    <strong>Analytics Providers:</strong> For understanding
                    service usage and performance
                  </li>
                </ul>

                <h3 className="text-xl font-semibold mb-3">
                  4.2 Legal Requirements
                </h3>
                <p className="text-gray-700 mb-4">
                  We may disclose your information when required by law or to:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Comply with legal processes or government requests</li>
                  <li>Protect our rights, property, or safety</li>
                  <li>Prevent fraud or security threats</li>
                  <li>Enforce our terms of service</li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  5. Data Security
                </h2>
                <p className="text-gray-700 mb-4">
                  We implement appropriate technical and organizational security
                  measures to protect your personal information:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Encryption of data in transit and at rest</li>
                  <li>Multi-tenant architecture with data isolation</li>
                  <li>Role-based access controls and authentication</li>
                  <li>Regular security updates and monitoring</li>
                  <li>
                    Secure password storage using industry-standard hashing
                  </li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  6. Data Retention
                </h2>
                <p className="text-gray-700 mb-4">
                  We retain your personal information for as long as necessary
                  to provide our services and comply with legal obligations:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    Account data: Until account deletion or 7 years after last
                    activity
                  </li>
                  <li>
                    Financial records: 7 years for legal and tax compliance
                  </li>
                  <li>
                    Usage analytics: Up to 2 years for service improvement
                  </li>
                  <li>
                    Email communications: Until you opt out or account deletion
                  </li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">7. Your Rights</h2>
                <p className="text-gray-700 mb-4">
                  You have the following rights regarding your personal data:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    <strong>Access:</strong> Request copies of your personal
                    information
                  </li>
                  <li>
                    <strong>Rectification:</strong> Request correction of
                    inaccurate data
                  </li>
                  <li>
                    <strong>Erasure:</strong> Request deletion of your personal
                    data (subject to legal requirements)
                  </li>
                  <li>
                    <strong>Portability:</strong> Export your data in common
                    formats (CSV, PDF)
                  </li>
                  <li>
                    <strong>Restriction:</strong> Request limitation of
                    processing in certain circumstances
                  </li>
                  <li>
                    <strong>Objection:</strong> Object to processing based on
                    legitimate interests
                  </li>
                </ul>
                <p className="text-gray-700">
                  To exercise these rights, please contact us at
                  privacy@arvalox.com.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  8. International Data Transfers
                </h2>
                <p className="text-gray-700 mb-4">
                  Arvalox operates globally and may transfer your personal
                  information to countries outside your jurisdiction. We ensure
                  appropriate safeguards are in place for such transfers,
                  including:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    Standard Contractual Clauses approved by relevant
                    authorities
                  </li>
                  <li>
                    Adequacy decisions for countries with appropriate data
                    protection laws
                  </li>
                  <li>
                    Certification schemes and codes of conduct where applicable
                  </li>
                </ul>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  9. Cookies and Tracking
                </h2>
                <p className="text-gray-700 mb-4">
                  We use cookies and similar technologies to enhance your
                  experience and analyze usage patterns. Types of cookies we
                  use:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>
                    <strong>Essential cookies:</strong> Necessary for basic
                    functionality and security
                  </li>
                  <li>
                    <strong>Performance cookies:</strong> Help us understand how
                    you use our service
                  </li>
                  <li>
                    <strong>Preference cookies:</strong> Remember your settings
                    and customizations
                  </li>
                </ul>
                <p className="text-gray-700">
                  You can control cookies through your browser settings, but
                  some features may not work properly if disabled.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  10. Children's Privacy
                </h2>
                <p className="text-gray-700">
                  Our services are not intended for individuals under 16 years
                  of age. We do not knowingly collect personal information from
                  children under 16. If we become aware that we have collected
                  such information, we will take steps to delete it promptly.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  11. Changes to This Privacy Policy
                </h2>
                <p className="text-gray-700 mb-4">
                  We may update this Privacy Policy periodically to reflect
                  changes in our practices or legal requirements. We will notify
                  you of any material changes by:
                </p>
                <ul className="list-disc pl-6 mb-4 text-gray-700">
                  <li>Posting the updated policy on our website</li>
                  <li>Sending email notification to registered users</li>
                  <li>Displaying prominent notices within our application</li>
                </ul>
                <p className="text-gray-700">
                  Changes become effective 30 days after posting unless
                  otherwise specified.
                </p>
              </section>

              <section>
                <h2 className="text-2xl font-semibold mb-4">
                  12. Contact Information
                </h2>
                <p className="text-gray-700 mb-4">
                  If you have questions, concerns, or requests regarding this
                  Privacy Policy or our data practices, please contact us:
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-gray-700 mb-2">
                    <strong>Email:</strong> privacy@arvalox.com
                  </p>
                  <p className="text-gray-700 mb-2">
                    <strong>Support:</strong> support@arvalox.com
                  </p>
                  <p className="text-gray-700 mb-2">
                    <strong>Data Protection Officer:</strong> dpo@arvalox.com
                  </p>
                </div>
                <p className="text-gray-700 mt-4">
                  We will respond to your inquiries within 30 days of receipt.
                </p>
              </section>

              <div className="border-t pt-6 mt-8">
                <p className="text-sm text-gray-500 text-center">
                  This Privacy Policy is effective as of{" "}
                  {new Date().toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}{" "}
                  and applies to all information collected by Arvalox.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
