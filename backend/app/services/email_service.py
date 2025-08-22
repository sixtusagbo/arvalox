import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.core.config import settings


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_host = settings.smtp_host
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email to one or more recipients
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = subject

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False

    async def send_password_reset_email(
        self, 
        to_email: str, 
        reset_token: str, 
        user_name: str,
        organization_name: str
    ) -> bool:
        """
        Send password reset email to user
        
        Args:
            to_email: Recipient email address
            reset_token: Password reset token
            user_name: User's full name
            organization_name: Organization name
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        # Create reset URL (you may need to adjust this based on your frontend URL)
        reset_url = f"http://localhost:3000/reset-password?token={reset_token}"
        
        subject = f"Password Reset Request - {organization_name}"
        
        # HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: #ffffff;
                    padding: 30px;
                    border: 1px solid #e9ecef;
                }}
                .button {{
                    display: inline-block;
                    background-color: #007bff;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                    border-radius: 0 0 8px 8px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                    padding: 15px;
                    border-radius: 4px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Password Reset Request</h1>
                <p>{organization_name}</p>
            </div>
            
            <div class="content">
                <p>Hello {user_name},</p>
                
                <p>We received a request to reset your password for your {organization_name} account. If you made this request, click the button below to reset your password:</p>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset Password</a>
                </div>
                
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #f8f9fa; padding: 10px; border-radius: 4px;">
                    {reset_url}
                </p>
                
                <div class="warning">
                    <strong>Important:</strong> This link will expire in 1 hour for security reasons. If you didn't request this password reset, please ignore this email and your password will remain unchanged.
                </div>
                
                <p>If you continue to have problems, please contact your system administrator.</p>
                
                <p>Best regards,<br>The {organization_name} Team</p>
            </div>
            
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; {organization_name}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
        
        # Plain text content
        text_content = f"""
        Password Reset Request - {organization_name}
        
        Hello {user_name},
        
        We received a request to reset your password for your {organization_name} account.
        
        To reset your password, please visit the following link:
        {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        If you didn't request this password reset, please ignore this email and your password will remain unchanged.
        
        If you continue to have problems, please contact your system administrator.
        
        Best regards,
        The {organization_name} Team
        
        ---
        This is an automated message. Please do not reply to this email.
        """
        
        return await self.send_email([to_email], subject, html_content, text_content)


# Create a singleton instance
email_service = EmailService()
