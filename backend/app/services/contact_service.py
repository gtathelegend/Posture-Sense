import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("posturesense.contact")


class EmailConfigError(Exception):
    """Raised when email service credentials or required environment variables are missing."""
    pass


class EmailDeliveryError(Exception):
    """Raised when SMTP connection or delivery fails."""
    pass


class ContactService:
    @staticmethod
    def _sanitize_header(value: str) -> str:
        """Strip control characters and newlines to prevent header injection."""
        if not value:
            return ""
        return str(value).replace("\r", "").replace("\n", "").strip()

    @classmethod
    def get_smtp_config(cls):
        """Retrieve and validate SMTP configuration parameters."""
        user = os.getenv('SMTP_USERNAME') or os.getenv('EMAIL_USER')
        password = os.getenv('SMTP_PASSWORD') or os.getenv('EMAIL_PASSWORD')
        admin_email = os.getenv('ADMIN_EMAIL') or os.getenv('MAIL_TO') or user
        mail_from = os.getenv('MAIL_FROM') or user or 'noreply@posturesense.ai'
        
        host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        port_val = os.getenv('SMTP_PORT', '587')
        try:
            port = int(port_val)
        except ValueError:
            port = 587

        timeout_val = os.getenv('SMTP_TIMEOUT', '10')
        try:
            timeout = float(timeout_val)
        except ValueError:
            timeout = 10.0

        use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() in ('true', '1', 'yes')
        use_ssl = os.getenv('SMTP_USE_SSL', 'false').lower() in ('true', '1', 'yes')

        return {
            'user': user,
            'password': password,
            'admin_email': admin_email,
            'mail_from': mail_from,
            'host': host,
            'port': port,
            'timeout': timeout,
            'use_tls': use_tls,
            'use_ssl': use_ssl,
        }

    @classmethod
    def is_configured(cls) -> bool:
        """Return True if required credentials exist for sending email."""
        config = cls.get_smtp_config()
        return bool(config['user'] and config['password'] and config['admin_email'])

    @classmethod
    def send_contact_email(cls, name: str, email: str, message: str) -> bool:
        """Send contact inquiry to admin and confirmation copy to user."""
        logger.info("contact.submit_started provider=smtp")
        if not cls.is_configured():
            logger.warning("contact.email_delivery_failed reason=unconfigured")
            raise EmailConfigError("Email service is not configured")

        config = cls.get_smtp_config()
        safe_name = cls._sanitize_header(name)
        safe_email = cls._sanitize_header(email)

        # Admin Notification Email
        msg_admin = MIMEMultipart()
        msg_admin['From'] = config['mail_from']
        msg_admin['To'] = config['admin_email']
        msg_admin['Subject'] = f"New Contact Message from {safe_name}"
        
        body_admin = f"""New Message from {safe_name}:

Email: {safe_email}
Message:
{message}
"""
        msg_admin.attach(MIMEText(body_admin, 'plain', 'utf-8'))

        # User Confirmation Email
        msg_user = MIMEMultipart()
        msg_user['From'] = config['mail_from']
        msg_user['To'] = safe_email
        msg_user['Subject'] = "Thank you for contacting PostureSense"
        
        body_user = f"""Hello {safe_name},

Thank you for contacting PostureSense! We have received your message and will get back to you shortly.

Your submitted message:
"{message}"

Best regards,
Team PostureSense
"""
        msg_user.attach(MIMEText(body_user, 'plain', 'utf-8'))

        logger.info("contact.email_delivery_started host=%s port=%s", config['host'], config['port'])

        try:
            if config['use_ssl']:
                with smtplib.SMTP_SSL(config['host'], config['port'], timeout=config['timeout']) as server:
                    server.login(config['user'], config['password'])
                    server.send_message(msg_admin)
                    server.send_message(msg_user)
            else:
                with smtplib.SMTP(config['host'], config['port'], timeout=config['timeout']) as server:
                    if config['use_tls']:
                        server.starttls()
                    server.login(config['user'], config['password'])
                    server.send_message(msg_admin)
                    server.send_message(msg_user)
            
            logger.info("contact.email_delivery_success status=sent")
            return True
        except (smtplib.SMTPException, OSError, TimeoutError) as e:
            logger.error("contact.email_delivery_failed error=%s", str(e))
            raise EmailDeliveryError(f"SMTP delivery failed: {str(e)}") from e

    @classmethod
    def send_subscription_email(cls, email: str) -> bool:
        """Send newsletter subscription notification."""
        logger.info("newsletter.submit_started provider=smtp")
        if not cls.is_configured():
            logger.warning("newsletter.email_delivery_failed reason=unconfigured")
            raise EmailConfigError("Email service is not configured")

        config = cls.get_smtp_config()
        safe_email = cls._sanitize_header(email)

        msg = MIMEMultipart()
        msg['From'] = config['mail_from']
        msg['To'] = config['admin_email']
        msg['Subject'] = "New Newsletter Subscription"
        
        body = f"""New newsletter subscription request:

Email: {safe_email}
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        try:
            if config['use_ssl']:
                with smtplib.SMTP_SSL(config['host'], config['port'], timeout=config['timeout']) as server:
                    server.login(config['user'], config['password'])
                    server.send_message(msg)
            else:
                with smtplib.SMTP(config['host'], config['port'], timeout=config['timeout']) as server:
                    if config['use_tls']:
                        server.starttls()
                    server.login(config['user'], config['password'])
                    server.send_message(msg)
            
            logger.info("newsletter.email_delivery_success status=sent")
            return True
        except (smtplib.SMTPException, OSError, TimeoutError) as e:
            logger.error("newsletter.email_delivery_failed error=%s", str(e))
            raise EmailDeliveryError(f"SMTP subscription delivery failed: {str(e)}") from e
