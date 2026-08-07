import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class ContactService:
    @staticmethod
    def send_contact_email(name, email, message):
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        receiver_email = os.getenv('ADMIN_EMAIL')
        
        # Message to Admin
        msg_admin = MIMEMultipart()
        msg_admin['From'] = sender_email
        msg_admin['To'] = receiver_email
        msg_admin['Subject'] = f"New Message from {name}"
        
        body_admin = f"""
        New Message from {name}:

        Email: {email}
        Message: {message}
        """
        msg_admin.attach(MIMEText(body_admin, 'plain'))
        
        # Message to User
        msg_user = MIMEMultipart()
        msg_user['From'] = sender_email
        msg_user['To'] = email
        msg_user['Subject'] = f"Thank you for contacting {name}"
        
        body_user = f"""
        Thank you for contacting us {name} !
        We will contact you shortly.
        Thanks,
        Team Posture Sense
        """
        msg_user.attach(MIMEText(body_user, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg_admin)
            server.send_message(msg_user)
            
        return True

    @staticmethod
    def send_subscription_email(email):
        sender_email = os.getenv('EMAIL_USER')
        sender_password = os.getenv('EMAIL_PASSWORD')
        receiver_email = os.getenv('ADMIN_EMAIL')
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = "New Newsletter Subscription"
        
        body = f"""
        New newsletter subscription:

        Email: {email}
        """
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        return True
