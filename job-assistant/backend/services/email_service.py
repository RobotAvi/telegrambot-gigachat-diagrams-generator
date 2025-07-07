import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self, user_email_config: Optional[Dict] = None):
        """Initialize email service with user's email configuration."""
        if user_email_config:
            self.smtp_server = user_email_config.get("smtp_server", "smtp.gmail.com")
            self.smtp_port = int(user_email_config.get("smtp_port", 587))
            self.email_address = user_email_config.get("email_address")
            self.email_password = user_email_config.get("email_password")
        else:
            # Use default configuration from environment
            self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", 587))
            self.email_address = os.getenv("EMAIL_ADDRESS")
            self.email_password = os.getenv("EMAIL_PASSWORD")
    
    async def send_job_application(
        self, 
        recipient_email: str, 
        job_title: str, 
        company: str, 
        cover_letter: str,
        resume_file_path: Optional[str] = None,
        user_name: str = "Соискатель"
    ) -> bool:
        """Send job application email with resume attachment."""
        
        subject = f"Отклик на вакансию {job_title}"
        
        # Create message
        message = MIMEMultipart()
        message["From"] = self.email_address
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Email body
        body = f"""
Здравствуйте!

Меня заинтересовала вакансия "{job_title}" в компании {company}.

{cover_letter}

С уважением,
{user_name}

--
Это письмо отправлено автоматически через Job Assistant.
        """
        
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Attach resume if provided
        if resume_file_path and os.path.exists(resume_file_path):
            try:
                with open(resume_file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                
                filename = os.path.basename(resume_file_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                
                message.attach(part)
            except Exception as e:
                print(f"Error attaching resume: {e}")
        
        return await self._send_email(message, recipient_email)
    
    async def send_hr_message(
        self, 
        recipient_email: str, 
        company: str,
        position: str,
        message_content: str,
        user_name: str = "Соискатель"
    ) -> bool:
        """Send direct message to HR manager."""
        
        subject = f"Интерес к позиции {position} в {company}"
        
        # Create message
        message = MIMEMultipart()
        message["From"] = self.email_address
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Email body
        body = f"""
Здравствуйте!

{message_content}

С уважением,
{user_name}

Контакты для связи:
Email: {self.email_address}

--
Это письмо отправлено автоматически через Job Assistant.
        """
        
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        return await self._send_email(message, recipient_email)
    
    async def send_follow_up_message(
        self,
        recipient_email: str,
        original_subject: str,
        follow_up_message: str,
        user_name: str = "Соискатель"
    ) -> bool:
        """Send follow-up message for previous application."""
        
        subject = f"Re: {original_subject}"
        
        # Create message
        message = MIMEMultipart()
        message["From"] = self.email_address
        message["To"] = recipient_email
        message["Subject"] = subject
        
        # Email body
        body = f"""
Здравствуйте!

{follow_up_message}

С уважением,
{user_name}

--
Это письмо отправлено автоматически через Job Assistant.
        """
        
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        return await self._send_email(message, recipient_email)
    
    async def _send_email(self, message: MIMEMultipart, recipient_email: str) -> bool:
        """Send email using SMTP."""
        if not self.email_address or not self.email_password:
            print("Email credentials not configured")
            return False
        
        try:
            # Create secure connection
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                
                text = message.as_string()
                server.sendmail(self.email_address, recipient_email, text)
            
            print(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email to {recipient_email}: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """Validate email configuration."""
        if not self.email_address or not self.email_password:
            return False
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
            return True
        except Exception as e:
            print(f"Email configuration validation failed: {e}")
            return False
    
    async def find_hr_emails(self, company: str) -> List[str]:
        """Find HR emails for a company (placeholder implementation)."""
        # This would implement actual HR email discovery logic
        # Could use LinkedIn, company websites, etc.
        
        common_hr_patterns = [
            f"hr@{company.lower().replace(' ', '')}.com",
            f"hr@{company.lower().replace(' ', '')}.ru",
            f"jobs@{company.lower().replace(' ', '')}.com",
            f"careers@{company.lower().replace(' ', '')}.com",
            f"recruiting@{company.lower().replace(' ', '')}.com"
        ]
        
        # In a real implementation, you would:
        # 1. Search LinkedIn for HR managers
        # 2. Check company website for contact info
        # 3. Use email finder services
        # 4. Validate email addresses
        
        return common_hr_patterns[:2]  # Return first 2 guesses