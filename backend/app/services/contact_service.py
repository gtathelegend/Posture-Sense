import os
import html
import logging
import requests

logger = logging.getLogger("posturesense.contact")

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


class EmailConfigError(Exception):
    """Raised when email service credentials or required environment variables are missing."""
    pass


class EmailDeliveryError(Exception):
    """Raised when email API connection or delivery fails."""
    pass


class ContactService:
    @staticmethod
    def _sanitize_header(value: str) -> str:
        """Strip control characters and newlines to prevent header injection."""
        if not value:
            return ""
        return str(value).replace("\r", "").replace("\n", "").strip()

    @classmethod
    def get_config(cls):
        """Retrieve and validate Brevo API configuration parameters."""
        raw_key = os.getenv('BREVO_API_KEY') or ''
        api_key = raw_key.strip().strip("'").strip('"')

        raw_sender = os.getenv('BREVO_SENDER_EMAIL') or ''
        sender_email = raw_sender.strip().strip("'").strip('"')

        raw_sender_name = os.getenv('BREVO_SENDER_NAME') or 'PostureSense'
        sender_name = raw_sender_name.strip().strip("'").strip('"')

        raw_recipient = os.getenv('CONTACT_RECIPIENT_EMAIL') or os.getenv('ADMIN_EMAIL') or ''
        recipient_email = raw_recipient.strip().strip("'").strip('"')

        timeout_val = os.getenv('BREVO_TIMEOUT', '10')
        try:
            timeout = float(str(timeout_val).strip())
        except ValueError:
            timeout = 10.0

        return {
            'api_key': api_key,
            'sender_email': sender_email,
            'sender_name': sender_name,
            'recipient_email': recipient_email,
            'timeout': timeout,
            'api_url': BREVO_API_URL
        }

    @classmethod
    def get_key_diagnostics(cls) -> dict:
        """Return safe diagnostic metadata about BREVO_API_KEY without revealing the key."""
        config = cls.get_config()
        key = config['api_key']
        return {
            'present': bool(key),
            'length': len(key),
            'has_prefix': key.startswith('xkeysib-')
        }

    @classmethod
    def is_configured(cls) -> bool:
        """Return True if required credentials exist for sending transactional email via Brevo."""
        config = cls.get_config()
        return bool(config['api_key'] and config['sender_email'] and config['recipient_email'])

    @classmethod
    def send_contact_email(cls, name: str, email: str, message: str) -> bool:
        """Send contact inquiry to recipient and support team via Brevo REST API."""
        logger.info("contact.submit_started provider=brevo")
        if not cls.is_configured():
            logger.warning("contact.email_delivery_failed reason=unconfigured provider=brevo")
            raise EmailConfigError("Email service is not configured")

        config = cls.get_config()
        safe_name = cls._sanitize_header(name)
        safe_email = cls._sanitize_header(email)

        escaped_name = html.escape(safe_name)
        escaped_email = html.escape(safe_email)
        escaped_message = html.escape(message).replace("\n", "<br>")

        text_content = f"""New contact message from {safe_name}:

Email: {safe_email}
Message:
{message}
"""

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>New Contact Form Submission</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; padding: 24px;">
  <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    <div style="border-bottom: 2px solid #06b6d4; padding-bottom: 16px; margin-bottom: 24px;">
      <h2 style="margin: 0; color: #0f172a; font-size: 20px;">New Contact Message &mdash; PostureSense</h2>
    </div>
    <table style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
      <tr>
        <td style="padding: 8px 0; color: #64748b; font-weight: 600; width: 100px;">From:</td>
        <td style="padding: 8px 0; color: #0f172a; font-weight: 500;">{escaped_name}</td>
      </tr>
      <tr>
        <td style="padding: 8px 0; color: #64748b; font-weight: 600;">Email:</td>
        <td style="padding: 8px 0; color: #0f172a;"><a href="mailto:{escaped_email}" style="color: #06b6d4; text-decoration: none;">{escaped_email}</a></td>
      </tr>
    </table>
    <div style="background: #f1f5f9; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
      <h4 style="margin: 0 0 12px 0; color: #475569; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Message</h4>
      <div style="color: #1e293b; font-size: 15px; white-space: pre-wrap;">{escaped_message}</div>
    </div>
    <div style="border-top: 1px solid #e2e8f0; padding-top: 16px; font-size: 12px; color: #94a3b8; text-align: center;">
      Sent via PostureSense Contact System &middot; Reply directly to this email to contact {escaped_name}.
    </div>
  </div>
</body>
</html>
"""

        payload = {
            "sender": {
                "name": config['sender_name'],
                "email": config['sender_email']
            },
            "to": [
                {
                    "email": config['recipient_email']
                }
            ],
            "replyTo": {
                "name": safe_name,
                "email": safe_email
            },
            "subject": f"New contact form submission from {safe_name}",
            "textContent": text_content,
            "htmlContent": html_content
        }

        headers = {
            "api-key": config['api_key'],
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        logger.info("contact.email_delivery_started provider=brevo")

        try:
            response = requests.post(
                config['api_url'],
                json=payload,
                headers=headers,
                timeout=config['timeout']
            )

            if 200 <= response.status_code < 300:
                logger.info("contact.email_delivery_success provider=brevo status_code=%d", response.status_code)
                return True
            else:
                err_reason = ""
                try:
                    res_json = response.json()
                    err_reason = res_json.get('message') or res_json.get('code') or ""
                except Exception:
                    err_reason = (response.text or "")[:150]

                logger.error(
                    "contact.email_delivery_failed provider=brevo status_code=%d reason=%s",
                    response.status_code,
                    err_reason
                )
                raise EmailDeliveryError(f"Brevo API returned status {response.status_code}: {err_reason}")

        except requests.RequestException as e:
            logger.error("contact.email_delivery_failed provider=brevo error=%s", type(e).__name__)
            raise EmailDeliveryError(f"Brevo delivery failed: {type(e).__name__}") from e
        except Exception as e:
            if isinstance(e, (EmailConfigError, EmailDeliveryError)):
                raise
            logger.error("contact.email_delivery_failed provider=brevo error=%s", type(e).__name__)
            raise EmailDeliveryError(f"Unexpected delivery failure: {type(e).__name__}") from e

    @classmethod
    def send_subscription_email(cls, email: str) -> bool:
        """Send newsletter subscription notification via Brevo REST API."""
        logger.info("newsletter.submit_started provider=brevo")
        if not cls.is_configured():
            logger.warning("newsletter.email_delivery_failed reason=unconfigured provider=brevo")
            raise EmailConfigError("Email service is not configured")

        config = cls.get_config()
        safe_email = cls._sanitize_header(email)
        escaped_email = html.escape(safe_email)

        text_content = f"New newsletter subscription request:\n\nEmail: {safe_email}\n"
        html_content = f"""<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; line-height: 1.5; color: #1e293b; padding: 20px;">
  <h3>New Newsletter Subscription &mdash; PostureSense</h3>
  <p><strong>Subscribed Email:</strong> <a href="mailto:{escaped_email}">{escaped_email}</a></p>
</body>
</html>
"""

        payload = {
            "sender": {
                "name": config['sender_name'],
                "email": config['sender_email']
            },
            "to": [
                {
                    "email": config['recipient_email']
                }
            ],
            "replyTo": {
                "email": safe_email
            },
            "subject": "New Newsletter Subscription",
            "textContent": text_content,
            "htmlContent": html_content
        }

        headers = {
            "api-key": config['api_key'],
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            response = requests.post(
                config['api_url'],
                json=payload,
                headers=headers,
                timeout=config['timeout']
            )

            if 200 <= response.status_code < 300:
                logger.info("newsletter.email_delivery_success provider=brevo status_code=%d", response.status_code)
                return True
            else:
                err_reason = ""
                try:
                    res_json = response.json()
                    err_reason = res_json.get('message') or res_json.get('code') or ""
                except Exception:
                    err_reason = (response.text or "")[:150]

                logger.error("newsletter.email_delivery_failed provider=brevo status_code=%d reason=%s", response.status_code, err_reason)
                raise EmailDeliveryError(f"Brevo API returned status {response.status_code}: {err_reason}")

        except requests.RequestException as e:
            logger.error("newsletter.email_delivery_failed provider=brevo error=%s", type(e).__name__)
            raise EmailDeliveryError(f"Brevo subscription delivery failed: {type(e).__name__}") from e
        except Exception as e:
            if isinstance(e, (EmailConfigError, EmailDeliveryError)):
                raise
            logger.error("newsletter.email_delivery_failed provider=brevo error=%s", type(e).__name__)
            raise EmailDeliveryError(f"Unexpected subscription failure: {type(e).__name__}") from e
