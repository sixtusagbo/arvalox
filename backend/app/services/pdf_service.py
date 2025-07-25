import io
from datetime import date
from decimal import Decimal
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable

from app.models.invoice import Invoice
from app.models.organization import Organization


class InvoicePDFService:
    """Service for generating professional invoice PDFs"""

    def __init__(self):
        self.page_size = A4
        self.margin = 0.75 * inch
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the invoice"""
        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            alignment=0,  # Left alignment
        ))

        # Invoice title style
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            alignment=2,  # Right alignment
        ))

        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=12,
            spaceAfter=6,
            leftIndent=0,
        ))

        # Address style
        self.styles.add(ParagraphStyle(
            name='Address',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=3,
            leftIndent=0,
        ))

        # Total style
        self.styles.add(ParagraphStyle(
            name='Total',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#2c3e50'),
            alignment=2,  # Right alignment
        ))

    def generate_invoice_pdf(
        self, 
        invoice: Invoice, 
        organization: Organization,
        customer_data: dict,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Generate a professional invoice PDF
        
        Args:
            invoice: Invoice model instance
            organization: Organization model instance
            customer_data: Customer information dict
            output_path: Optional file path to save PDF
            
        Returns:
            PDF content as bytes
        """
        # Create PDF buffer
        buffer = io.BytesIO()
        
        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.page_size,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        # Build PDF content
        story = []
        
        # Header section
        story.extend(self._build_header(organization, invoice))
        story.append(Spacer(1, 0.2 * inch))
        
        # Bill to section
        story.extend(self._build_bill_to_section(customer_data))
        story.append(Spacer(1, 0.2 * inch))
        
        # Invoice details section
        story.extend(self._build_invoice_details(invoice))
        story.append(Spacer(1, 0.3 * inch))
        
        # Line items table
        story.extend(self._build_line_items_table(invoice))
        story.append(Spacer(1, 0.2 * inch))
        
        # Totals section
        story.extend(self._build_totals_section(invoice))
        story.append(Spacer(1, 0.3 * inch))
        
        # Notes section
        if invoice.notes:
            story.extend(self._build_notes_section(invoice))
            story.append(Spacer(1, 0.2 * inch))
        
        # Footer section
        story.extend(self._build_footer(organization))
        
        # Build PDF
        doc.build(story)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Save to file if path provided
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
        
        return pdf_content

    def _build_header(self, organization: Organization, invoice: Invoice) -> list:
        """Build the header section with company info and invoice title"""
        elements = []
        
        # Create header table with company info and invoice title
        header_data = [
            [
                Paragraph(organization.name, self.styles['CompanyName']),
                Paragraph(f"INVOICE", self.styles['InvoiceTitle'])
            ]
        ]
        
        header_table = Table(header_data, colWidths=[4 * inch, 3 * inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(header_table)
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3498db')))
        
        return elements

    def _build_bill_to_section(self, customer_data: dict) -> list:
        """Build the bill to section with customer information"""
        elements = []
        
        # Bill to header
        elements.append(Paragraph("Bill To:", self.styles['SectionHeader']))
        
        # Customer information
        customer_info = [
            customer_data.get('contact_name', ''),
            customer_data.get('billing_address', ''),
            customer_data.get('email', ''),
            customer_data.get('phone', ''),
        ]
        
        for info in customer_info:
            if info:
                elements.append(Paragraph(info, self.styles['Address']))
        
        return elements

    def _build_invoice_details(self, invoice: Invoice) -> list:
        """Build the invoice details section"""
        elements = []
        
        # Invoice details table
        details_data = [
            ['Invoice Number:', invoice.invoice_number],
            ['Invoice Date:', invoice.invoice_date.strftime('%B %d, %Y')],
            ['Due Date:', invoice.due_date.strftime('%B %d, %Y')],
            ['Status:', invoice.status.title()],
        ]
        
        details_table = Table(details_data, colWidths=[1.5 * inch, 2 * inch])
        details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
        ]))
        
        elements.append(details_table)
        
        return elements

    def _build_line_items_table(self, invoice: Invoice) -> list:
        """Build the line items table"""
        elements = []
        
        # Table headers
        headers = ['Description', 'Quantity', 'Unit Price', 'Total']
        table_data = [headers]
        
        # Add line items
        for item in invoice.items:
            row = [
                item.description,
                f"{item.quantity:,.2f}",
                f"${item.unit_price:,.2f}",
                f"${item.line_total:,.2f}"
            ]
            table_data.append(row)
        
        # Create table
        col_widths = [3.5 * inch, 1 * inch, 1.25 * inch, 1.25 * inch]
        items_table = Table(table_data, colWidths=col_widths)
        
        # Style the table
        items_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            
            # Data rows styling
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(items_table)
        
        return elements

    def _build_totals_section(self, invoice: Invoice) -> list:
        """Build the totals section"""
        elements = []
        
        # Totals data
        totals_data = [
            ['Subtotal:', f"${invoice.subtotal:,.2f}"],
            ['Tax:', f"${invoice.tax_amount:,.2f}"],
            ['Total:', f"${invoice.total_amount:,.2f}"],
        ]
        
        if invoice.paid_amount > 0:
            totals_data.append(['Paid:', f"${invoice.paid_amount:,.2f}"])
            balance = invoice.total_amount - invoice.paid_amount
            totals_data.append(['Balance Due:', f"${balance:,.2f}"])
        
        # Create totals table (right-aligned)
        totals_table = Table(totals_data, colWidths=[1.5 * inch, 1.5 * inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            
            # Make total row stand out
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#3498db')),
        ]))
        
        # Right-align the totals table
        totals_wrapper = Table([[totals_table]], colWidths=[7 * inch])
        totals_wrapper.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
        ]))
        
        elements.append(totals_wrapper)
        
        return elements

    def _build_notes_section(self, invoice: Invoice) -> list:
        """Build the notes section"""
        elements = []
        
        elements.append(Paragraph("Notes:", self.styles['SectionHeader']))
        elements.append(Paragraph(invoice.notes, self.styles['Normal']))
        
        return elements

    def _build_footer(self, organization: Organization) -> list:
        """Build the footer section"""
        elements = []
        
        # Add some space before footer
        elements.append(Spacer(1, 0.5 * inch))
        
        # Footer line
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#bdc3c7')))
        
        # Footer text
        footer_text = f"Thank you for your business! | {organization.name}"
        if hasattr(organization, 'email') and organization.email:
            footer_text += f" | {organization.email}"
        
        footer_style = ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=1,  # Center alignment
            spaceAfter=0,
        )
        
        elements.append(Paragraph(footer_text, footer_style))
        
        return elements
