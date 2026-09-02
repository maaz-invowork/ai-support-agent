import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings


class EmailService:
    """Handle sending emails via SMTP."""

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None,
    ) -> bool:
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL
            msg["To"] = to_email

            # Attach plain text and HTML versions
            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send via SMTP
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    def send_order_cancellation_email(user_email: str, order_id: str, reason: str) -> bool:
        subject = f"Order {order_id} Cancellation Confirmation"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Order Cancellation Confirmed</h2>
                    <p>Dear Customer,</p>
                    <p>Your order has been successfully cancelled.</p>
                    
                    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p><strong>Order ID:</strong> {order_id}</p>
                        <p><strong>Cancellation Reason:</strong> {reason}</p>
                    </div>
                    
                    <p>If you have any questions about your cancellation, please don't hesitate to contact our support team.</p>
                    <p>Thank you for choosing our service.</p>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ccc;">
                    <p style="font-size: 12px; color: #666;">
                        This is an automated message. Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_content = f"""
        Order Cancellation Confirmed
        
        Dear Customer,
        
        Your order has been successfully cancelled.
        
        Order ID: {order_id}
        Cancellation Reason: {reason}
        
        If you have any questions about your cancellation, please don't hesitate to contact our support team.
        
        Thank you for choosing our service.
        """
        
        return EmailService.send_email(user_email, subject, html_content, text_content)
