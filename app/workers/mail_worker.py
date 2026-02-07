from celery import Celery

import smtplib
from email.message import EmailMessage
from pydantic import EmailStr

import os
from dotenv import load_dotenv
load_dotenv()

from app.utils.templates import render_template



app = Celery('my_tasks', 
             broker='redis://redis:6379/0',
             backend='redis://redis:6379/0')

@app.task
def send_email(to_email: EmailStr, subject: str, template_name: str, context: dict):
    # Рендерим html с подстановкой данных
    html_content = render_template(template_name, context)

    message = EmailMessage()
    message["From"] = os.getenv("SMTP_FROM")
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    smtplib.send(
        message,
        hostname=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT")),
        start_tls=True,
        username=os.getenv("SMTP_USERNAME"),
        password=os.getenv("SMTP_PASSWORD"),
    )