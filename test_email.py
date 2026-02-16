import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def test_email():
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")
    
    print(f"Sender: {sender}")
    # print(f"Password: {password}") # Do not print password
    print(f"Recipient: {recipient}")

    if not all([sender, password, recipient]):
        print("Credentials missing!")
        return

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = "Test Email from YouTube Report Agent"
    
    body = "This is a test email to verify credentials and delivery."
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print("Connecting to SMTP server...")
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("Logging in...")
            server.login(sender, password)
            print("Sending message...")
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_email()
