import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional, Tuple
import time
from .settings import settings
from .rate_limit import RateLimiter

class EmailMailer:
    """Handle SMTP email sending with retry logic and rate limiting."""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = None, 
                 smtp_user: str = None, smtp_pass: str = None):
        """
        Initialize mailer with SMTP settings.
        
        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_user: SMTP username/email
            smtp_pass: SMTP password/app password
        """
        self.smtp_host = smtp_host or settings.SMTP_HOST
        self.smtp_port = smtp_port or settings.SMTP_PORT
        self.smtp_user = smtp_user or settings.SMTP_USER
        self.smtp_pass = smtp_pass or settings.SMTP_PASS
        self.sender_name = settings.SENDER_NAME
        self.reply_to = settings.REPLY_TO
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(settings.RATE_PER_MIN)
        
        # Validate settings
        if not all([self.smtp_user, self.smtp_pass]):
            raise ValueError("SMTP credentials not configured")
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test SMTP connection.
        
        Returns:
            Tuple of (success, message)
        """
        try:
            with self._create_smtp_connection() as server:
                server.login(self.smtp_user, self.smtp_pass)
                return True, "SMTP connection successful"
        except Exception as e:
            return False, f"SMTP connection failed: {str(e)}"
    
    def _create_smtp_connection(self):
        """Create SMTP connection with proper security."""
        context = ssl.create_default_context()
        
        if self.smtp_port == 587:
            # Use STARTTLS
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls(context=context)
        elif self.smtp_port == 465:
            # Use SSL
            server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context)
        else:
            # Plain connection (not recommended)
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        
        return server
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   body_type: str = 'plain', from_name: str = None,
                   reply_to: str = None, attachments: List[str] = None) -> Tuple[bool, str]:
        """
        Send a single email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body content
            body_type: 'plain' or 'html'
            from_name: Custom sender name
            reply_to: Reply-to email address
            attachments: List of file paths to attach
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Create message
            msg = self._create_message(to_email, subject, body, body_type, from_name, reply_to)
            
            # Add attachments if any
            if attachments:
                self._add_attachments(msg, attachments)
            
            # Send email
            with self._create_smtp_connection() as server:
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            
            return True, "Email sent successfully"
            
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def _create_message(self, to_email: str, subject: str, body: str, 
                       body_type: str, from_name: str = None, reply_to: str = None) -> MIMEMultipart:
        """Create email message with proper headers."""
        msg = MIMEMultipart('alternative')
        
        # Set headers
        from_name = from_name or self.sender_name
        msg['From'] = f"{from_name} <{self.smtp_user}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if reply_to or self.reply_to:
            msg['Reply-To'] = reply_to or self.reply_to
        
        # Add body
        if body_type.lower() == 'html':
            html_part = MIMEText(body, 'html')
            msg.attach(html_part)
            
            # Also add plain text version for compatibility
            plain_body = self._html_to_plain(body)
            text_part = MIMEText(plain_body, 'plain')
            msg.attach(text_part)
        else:
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
        
        return msg
    
    def _html_to_plain(self, html_content: str) -> str:
        """Convert HTML content to plain text (basic implementation)."""
        import re
        
        # Remove HTML tags
        plain = re.sub(r'<[^>]+>', '', html_content)
        
        # Decode HTML entities
        plain = plain.replace('&nbsp;', ' ')
        plain = plain.replace('&amp;', '&')
        plain = plain.replace('&lt;', '<')
        plain = plain.replace('&gt;', '>')
        plain = plain.replace('&quot;', '"')
        
        # Clean up whitespace
        plain = re.sub(r'\s+', ' ', plain)
        plain = plain.strip()
        
        return plain
    
    def _add_attachments(self, msg: MIMEMultipart, attachments: List[str]) -> None:
        """Add file attachments to email message."""
        for file_path in attachments:
            try:
                with open(file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                
                # Add header
                filename = file_path.split('/')[-1]
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                
                msg.attach(part)
                
            except Exception as e:
                # Log attachment error but continue with email
                print(f"Warning: Could not attach {file_path}: {e}")
    
    def send_bulk_emails(self, recipients: List[Dict], subject: str, body: str,
                         body_type: str = 'plain', from_name: str = None,
                         reply_to: str = None, attachments: List[str] = None,
                         continue_on_error: bool = True, max_retries: int = 3) -> Dict:
        """
        Send bulk emails with progress tracking.
        
        Args:
            recipients: List of recipient dictionaries with 'email' key
            subject: Email subject
            body: Email body content
            body_type: 'plain' or 'html'
            from_name: Custom sender name
            reply_to: Reply-to email address
            attachments: List of file paths to attach
            continue_on_error: Whether to continue if some emails fail
            max_retries: Maximum retry attempts for failed emails
            
        Returns:
            Dictionary with results summary
        """
        total_recipients = len(recipients)
        successful = 0
        failed = 0
        errors = []
        
        print(f"Starting bulk email campaign to {total_recipients} recipients...")
        
        for i, recipient in enumerate(recipients, 1):
            email = recipient.get('email', '')
            if not email:
                failed += 1
                errors.append(f"Recipient {i}: No email address")
                continue
            
            # Try to send with retries
            success = False
            error_msg = ""
            
            for attempt in range(max_retries):
                success, message = self.send_email(
                    email, subject, body, body_type, from_name, reply_to, attachments
                )
                
                if success:
                    break
                else:
                    error_msg = message
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
            
            if success:
                successful += 1
                print(f"✓ Sent to {email} ({i}/{total_recipients})")
            else:
                failed += 1
                errors.append(f"Recipient {i} ({email}): {error_msg}")
                print(f"✗ Failed to send to {email}: {error_msg}")
                
                if not continue_on_error:
                    print("Stopping due to error...")
                    break
        
        # Summary
        summary = {
            'total': total_recipients,
            'successful': successful,
            'failed': failed,
            'success_rate': round((successful / total_recipients) * 100, 1) if total_recipients > 0 else 0,
            'errors': errors
        }
        
        print(f"\nCampaign completed: {successful}/{total_recipients} emails sent successfully")
        return summary
    
    def set_rate_limit(self, emails_per_minute: int) -> None:
        """
        Update rate limiting.
        
        Args:
            emails_per_minute: New rate limit
        """
        self.rate_limiter.set_rate(emails_per_minute)
        print(f"Rate limit set to {emails_per_minute} emails per minute")
    
    def get_rate_limit_info(self) -> Dict:
        """
        Get current rate limiting information.
        
        Returns:
            Dictionary with rate limit info
        """
        return {
            'emails_per_minute': self.rate_limiter.get_current_rate(),
            'estimated_completion_time': self.rate_limiter.estimate_completion_time(100)  # Example for 100 emails
        } 