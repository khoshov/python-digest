import smtplib
from pathlib import Path
from typing import List, Dict, Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

from config import settings
from logger.logger import setup_logger

logger = setup_logger(module_name=__name__)


class EmailService:
    """
    Модуль для отправки email уведомлений с результатами SMM pipeline.
    """

    def create_email_content(
        self, posts: List[Dict[str, str]], total_count: int
    ) -> str:
        """
        Создает HTML-содержимое письма с результатами pipeline.

        Args:
            posts: Список созданных постов
            total_count: Общее количество постов

        Returns:
            str: HTML-содержимое письма
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #306998; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .post {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .post-title {{ font-size: 18px; font-weight: bold; color: #306998; margin-bottom: 5px; }}
                .post-type {{ font-size: 14px; color: #666; margin-bottom: 10px; font-style: italic; }}
                .post-url {{ color: #0066cc; text-decoration: none; }}
                .post-content {{ margin-top: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
                .stats {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ margin-top: 30px; padding: 15px; background-color: #f5f5f5; border-radius: 5px; text-align: center; }}
                .python-accent {{ color: #306998; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🐍 Python Digest - Еженедельный дайджест</h1>
                <p>Лучшее из мира Python-разработки за неделю</p>
                <p>Сгенерировано: {datetime.now().strftime("%d.%m.%Y в %H:%M")}</p>
            </div>

            <div class="stats">
                <h2>📊 Статистика дайджеста</h2>
                <ul>
                    <li><strong>Всего материалов отобрано:</strong> {total_count}</li>
                    <li><strong>Период сбора:</strong> последние 7 дней</li>
                    <li><strong>Источники:</strong> Python-сообщества, блоги, новостные ленты</li>
                    <li><strong>Постов с изображениями:</strong> {len([p for p in posts if p.get("image_path")])}</li>
                </ul>
            </div>
        """

        if posts:
            html_content += "<h2>🐍 Python-материалы этой недели (сортировка по релевантности):</h2>"

            for idx, post in enumerate(posts, 1):
                # Получаем данные поста согласно ТЗ
                title = post.get("title", "Без названия")[:100]  # Максимум 100 символов
                post_type = post.get(
                    "content_type", "Материал"
                )  # Тип: статья, новость, видео и т.д.
                description = post.get("description", post.get("post_content", ""))[
                    :350
                ]  # Максимум 350 символов
                url = post.get("url", "#")

                html_content += f"""
                <div class="post">
                    <div class="post-title">{idx}. {title}</div>
                    <div class="post-type">Тип материала: {post_type}</div>
                    <div class="post-content">
                        {description.replace(chr(10), "<br>")}
                    </div>
                    <p style="margin-top: 15px;">
                        <strong>🔗 Ссылка:</strong> <a href="{url}" class="post-url">{url}</a>
                    </p>
                    {f"<p><strong>🖼️ Изображение:</strong> {Path(post['image_path']).name}</p>" if post.get("image_path") else ""}
                </div>
                """
        else:
            html_content += """
            <div class="post">
                <p>😔 На этой неделе не найдено интересных Python-материалов.</p>
                <p>💡 Возможно, стоит расширить источники или изменить критерии отбора.</p>
            </div>
            """

        html_content += """
            <div class="footer">
                <p><span class="python-accent">Автоматически сгенерировано Python Digest Pipeline</span></p>
                <p>🐍🤖 Powered by Python & AI</p>
                <p style="font-size: 12px; color: #666;">
                    Для инженеров Python • Каждую неделю • Самое интересное
                </p>
            </div>
        </body>
        </html>
        """

        return html_content

    def send_email_notification(
        self,
        posts: List[Dict[str, str]],
        markdown_file: Optional[Path] = None,
        summary_file: Optional[Path] = None,
        comprehensive_report: Optional[Path] = None,
    ) -> bool:
        """
        Отправляет email уведомление с результатами pipeline.

        Args:
            posts: Список созданных постов
            markdown_file: Путь к markdown файлу с результатами
            summary_file: Путь к файлу с краткой сводкой
            comprehensive_report: Путь к подробному отчету

        Returns:
            bool: True если отправка прошла успешно
        """
        if not settings.enable_email_sending:
            logger.info("📧 Отправка email отключена в настройках")
            return True

        if not settings.email_recipients:
            logger.warning("📧 Не указаны получатели email")
            return False

        try:
            logger.info("📧 Подготовка email уведомления...")

            # Создаем сообщение
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.email_from or settings.smtp_username
            msg["To"] = ", ".join(settings.email_recipients)
            msg["Subject"] = (
                f"{settings.email_subject} ({datetime.now().strftime('%d.%m.%Y %H:%M')})"
            )

            # Создаем HTML содержимое
            html_content = self.create_email_content(posts, len(posts))
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # Прикрепляем файлы если они есть
            attachments_added = 0

            if markdown_file and markdown_file.exists():
                with open(markdown_file, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {markdown_file.name}",
                    )
                    msg.attach(part)
                    attachments_added += 1

            if summary_file and summary_file.exists():
                with open(summary_file, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {summary_file.name}",
                    )
                    msg.attach(part)
                    attachments_added += 1

            if comprehensive_report and comprehensive_report.exists():
                with open(comprehensive_report, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {comprehensive_report.name}",
                    )
                    msg.attach(part)
                    attachments_added += 1

            # Подключаемся к SMTP серверу и отправляем
            logger.info(
                f"📧 Подключение к SMTP серверу: {settings.smtp_server}:{settings.smtp_port}"
            )

            try:
                with smtplib.SMTP(
                    settings.smtp_server, settings.smtp_port, timeout=30
                ) as server:
                    if settings.smtp_use_tls:
                        logger.debug("📧 Включаем TLS...")
                        server.starttls()

                    if settings.smtp_username and settings.smtp_password:
                        logger.debug("📧 Авторизация...")
                        server.login(settings.smtp_username, settings.smtp_password)

                    text = msg.as_string()
                    logger.debug("📧 Отправляем письмо...")
                    server.sendmail(msg["From"], settings.email_recipients, text)

            except smtplib.SMTPConnectError as e:
                logger.error(f"📧 Ошибка подключения к SMTP серверу: {e}")
                logger.error("💡 Проверьте настройки SMTP_SERVER и SMTP_PORT")
                return False
            except smtplib.SMTPAuthenticationError as e:
                logger.error(f"📧 Ошибка авторизации SMTP: {e}")
                logger.error(
                    "💡 Проверьте SMTP_USERNAME и SMTP_PASSWORD (для Gmail используйте App Password)"
                )
                return False
            except smtplib.SMTPException as e:
                logger.error(f"📧 SMTP ошибка: {e}")
                return False
            except ConnectionError as e:
                logger.error(f"📧 Ошибка сетевого соединения: {e}")
                logger.error(
                    "💡 Проверьте интернет-подключение и настройки брандмауэра"
                )
                return False

            logger.success("📧 Email успешно отправлен!")
            logger.info(f"   📤 Получатели: {', '.join(settings.email_recipients)}")
            logger.info(f"   📎 Вложений: {attachments_added}")
            logger.info(f"   📊 Постов в отчете: {len(posts)}")

            return True

        except Exception as e:
            logger.error(f"📧 Ошибка при отправке email: {e}")
            logger.exception("Детали ошибки:")
            return False

    def validate_email_configuration(self) -> bool:
        """
        Проверяет корректность настроек email.

        Returns:
            bool: True если настройки корректны
        """
        if not settings.enable_email_sending:
            return True

        missing = []

        # Обязательные настройки
        if not settings.smtp_server:
            missing.append("SMTP_SERVER")
        if not settings.smtp_username:
            missing.append("SMTP_USERNAME")
        if not settings.smtp_password:
            missing.append("SMTP_PASSWORD")
        if not settings.email_recipients:
            missing.append("EMAIL_RECIPIENTS")

        if missing:
            logger.error(f"❌ Отсутствуют настройки email: {', '.join(missing)}")
            return False

        # Проверяем email адреса
        invalid_emails = []
        for email in settings.email_recipients:
            if "@" not in email or "." not in email:
                invalid_emails.append(email)

        if invalid_emails:
            logger.error(f"❌ Некорректные email адреса: {', '.join(invalid_emails)}")
            return False

        logger.info("✅ Настройки email проверены")
        return True
