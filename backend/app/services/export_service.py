import csv
import io
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.services.aging_report_service import AgingReportService
from app.services.dashboard_service import DashboardService
from app.services.payment_history_service import PaymentHistoryService


class ExportService:
    """Service for exporting data in various formats (CSV, PDF, Excel)"""

    def __init__(self, db):
        self.db = db
        self.aging_service = AgingReportService(db)
        self.dashboard_service = DashboardService(db)
        self.payment_service = PaymentHistoryService(db)

    async def export_aging_report_csv(
        self,
        organization_id: int,
        as_of_date: Optional[date] = None,
        customer_id: Optional[int] = None,
        include_paid: bool = False,
    ) -> bytes:
        """Export aging report as CSV"""
        
        # Get aging report data
        report = await self.aging_service.generate_aging_report(
            organization_id=organization_id,
            as_of_date=as_of_date,
            customer_id=customer_id,
            include_paid=include_paid,
        )
        
        # Create CSV buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Invoice Number',
            'Customer Name',
            'Company Name',
            'Invoice Date',
            'Due Date',
            'Total Amount',
            'Paid Amount',
            'Outstanding Amount',
            'Days Overdue',
            'Aging Bucket',
            'Status'
        ])
        
        # Write invoice details
        for invoice in report['invoice_details']:
            writer.writerow([
                invoice['invoice_number'],
                invoice['customer_name'],
                invoice['company_name'] or '',
                invoice['invoice_date'].strftime('%Y-%m-%d'),
                invoice['due_date'].strftime('%Y-%m-%d'),
                float(invoice['total_amount']),
                float(invoice['paid_amount']),
                float(invoice['outstanding_amount']),
                invoice['days_overdue'],
                invoice['aging_bucket'],
                invoice['status']
            ])
        
        # Convert to bytes
        csv_content = output.getvalue().encode('utf-8')
        output.close()
        
        return csv_content

    async def export_aging_report_pdf(
        self,
        organization_id: int,
        as_of_date: Optional[date] = None,
        customer_id: Optional[int] = None,
        include_paid: bool = False,
    ) -> bytes:
        """Export aging report as PDF"""
        
        # Get aging report data
        report = await self.aging_service.generate_aging_report(
            organization_id=organization_id,
            as_of_date=as_of_date,
            customer_id=customer_id,
            include_paid=include_paid,
        )
        
        # Create PDF buffer
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Center
        )
        
        # Build PDF content
        story = []
        
        # Title
        story.append(Paragraph("Accounts Receivable Aging Report", title_style))
        story.append(Paragraph(f"As of: {report['report_date'].strftime('%B %d, %Y')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Summary table
        summary_data = [
            ['Aging Period', 'Count', 'Amount'],
            ['Current', str(report['summary']['current']['count']), f"${report['summary']['current']['amount']:,.2f}"],
            ['1-30 Days', str(report['summary']['days_1_30']['count']), f"${report['summary']['days_1_30']['amount']:,.2f}"],
            ['31-60 Days', str(report['summary']['days_31_60']['count']), f"${report['summary']['days_31_60']['amount']:,.2f}"],
            ['61-90 Days', str(report['summary']['days_61_90']['count']), f"${report['summary']['days_61_90']['amount']:,.2f}"],
            ['Over 90 Days', str(report['summary']['days_over_90']['count']), f"${report['summary']['days_over_90']['amount']:,.2f}"],
            ['Total', str(report['summary']['total']['count']), f"${report['summary']['total']['amount']:,.2f}"],
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Invoice details table (first 50 invoices to avoid huge PDFs)
        if report['invoice_details']:
            story.append(Paragraph("Invoice Details", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            details_data = [['Invoice #', 'Customer', 'Due Date', 'Outstanding', 'Days Overdue']]
            
            for invoice in report['invoice_details'][:50]:  # Limit to first 50
                details_data.append([
                    invoice['invoice_number'],
                    invoice['customer_name'][:20] + ('...' if len(invoice['customer_name']) > 20 else ''),
                    invoice['due_date'].strftime('%m/%d/%Y'),
                    f"${invoice['outstanding_amount']:,.2f}",
                    str(invoice['days_overdue'])
                ])
            
            details_table = Table(details_data, colWidths=[1.2*inch, 1.8*inch, 1*inch, 1*inch, 0.8*inch])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(details_table)
            
            if len(report['invoice_details']) > 50:
                story.append(Spacer(1, 12))
                story.append(Paragraph(f"Note: Showing first 50 of {len(report['invoice_details'])} invoices. Export CSV for complete data.", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content

    async def export_payment_history_csv(
        self,
        organization_id: int,
        customer_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 1000,
    ) -> bytes:
        """Export payment history as CSV"""
        
        # Get payment history data
        payment_history, total = await self.payment_service.get_payment_history(
            organization_id=organization_id,
            customer_id=customer_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=0,
        )
        
        # Create CSV buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Payment ID',
            'Payment Date',
            'Amount',
            'Payment Method',
            'Reference Number',
            'Status',
            'Invoice Number',
            'Customer Name',
            'Company Name',
            'Recorded By',
            'Created At'
        ])
        
        # Write payment data
        for payment in payment_history:
            writer.writerow([
                payment['payment_id'],
                payment['payment_date'].strftime('%Y-%m-%d'),
                float(payment['amount']),
                payment['payment_method'],
                payment['reference_number'] or '',
                payment['status'],
                payment['invoice']['invoice_number'] if payment['invoice'] else '',
                payment['invoice']['customer']['contact_name'] if payment['invoice'] and payment['invoice']['customer'] else '',
                payment['invoice']['customer']['company_name'] if payment['invoice'] and payment['invoice']['customer'] else '',
                payment['recorded_by']['email'] if payment['recorded_by'] else '',
                payment['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Convert to bytes
        csv_content = output.getvalue().encode('utf-8')
        output.close()
        
        return csv_content

    async def export_dashboard_data_csv(
        self,
        organization_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> bytes:
        """Export dashboard data as CSV"""
        
        # Get dashboard data
        dashboard_data = await self.dashboard_service.get_dashboard_overview(
            organization_id=organization_id,
            date_from=date_from,
            date_to=date_to,
        )
        
        # Create CSV buffer
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write dashboard summary
        writer.writerow(['Dashboard Summary'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Revenue', float(dashboard_data['revenue_metrics']['total_revenue'])])
        writer.writerow(['Outstanding Amount', float(dashboard_data['revenue_metrics']['outstanding_amount'])])
        writer.writerow(['Revenue Growth %', dashboard_data['revenue_metrics']['revenue_growth_percentage']])
        writer.writerow(['Collection Efficiency %', dashboard_data['aging_metrics']['collection_efficiency']])
        writer.writerow(['Total Customers', dashboard_data['customer_metrics']['total_customers']])
        writer.writerow(['Active Customers', dashboard_data['customer_metrics']['active_customers']])
        writer.writerow(['Overdue Amount', float(dashboard_data['aging_metrics']['total_overdue'])])
        writer.writerow([])
        
        # Write top customers
        writer.writerow(['Top Customers by Revenue'])
        writer.writerow(['Customer Name', 'Company Name', 'Total Revenue', 'Invoice Count', 'Outstanding Amount'])
        for customer in dashboard_data['top_customers']:
            writer.writerow([
                customer['contact_name'],
                customer['company_name'] or '',
                float(customer['total_revenue']),
                customer['invoice_count'],
                float(customer['outstanding_amount'])
            ])
        
        # Convert to bytes
        csv_content = output.getvalue().encode('utf-8')
        output.close()
        
        return csv_content

    def get_export_filename(self, export_type: str, format: str, organization_id: int) -> str:
        """Generate appropriate filename for export"""
        today = date.today().strftime('%Y%m%d')
        return f"{export_type}_org{organization_id}_{today}.{format}"

    def get_content_type(self, format: str) -> str:
        """Get appropriate content type for format"""
        content_types = {
            'csv': 'text/csv',
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        return content_types.get(format, 'application/octet-stream')
