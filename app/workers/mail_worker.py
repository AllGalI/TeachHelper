from celery import Celery

import smtplib
from email.message import EmailMessage

import os
from dotenv import load_dotenv
load_dotenv()

from app.utils.templates import render_template


app = Celery('my_tasks')

@app.task
def send_email(to_email: str, subject: str, template_name: str, context: dict):
    print("start send")
    # 1. Рендерим HTML (убедись, что render_template тоже синхронная)
    html_content = render_template(template_name, context)

    # 2. Формируем сообщение
    message = EmailMessage()
    message["From"] = os.getenv("SMTP_FROM")
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(html_content, subtype="html")

    # 3. Отправка через SMTP-сессию
    try:
        # Используем контекстный менеджер with, чтобы соединение закрылось само
        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls()  # Включаем шифрование
            server.login(os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD"))
            server.send_message(message)

    except Exception as e:
        # Для Celery важно видеть ошибки, чтобы он мог переотправить задачу (retry)
        print(f"Error sending email: {e}")
        raise e

