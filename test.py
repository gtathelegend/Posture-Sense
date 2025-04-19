import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

sender_email = os.getenv('EMAIL_USER')
sender_password = os.getenv('EMAIL_PASSWORD')
admin_email = os.getenv('ADMIN_EMAIL')

try:
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = admin_email
    msg['Subject'] = "Test Email"
    msg.attach(MIMEText("This is a test email.", 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
    print("Email sent successfully!")
except Exception as e:
    print(f"Error: {str(e)}")