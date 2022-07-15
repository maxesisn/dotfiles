import smtplib
from email.mime.text import MIMEText
from email.header import Header

from global_config import sender_pass, sender, receivers, sender_name, smtp_server

def send_mail(title, msg):
    message = MIMEText(msg.encode('utf-8'), 'plain', 'utf-8')
    message['From'] = str(Header(f"{sender_name} <{sender}>"))
    message['To'] = ", ".join(receivers)

    message['Subject'] = Header(title, 'utf-8')

    smtpObj = smtplib.SMTP_SSL(f"{smtp_server}:465")
    smtpObj.login(sender, sender_pass)
    smtpObj.sendmail(sender, receivers, message.as_string())