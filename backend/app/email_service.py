import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
from sqlalchemy.orm import Session
from .models import User, UserArticleCount, Article, EmailSettings
from .pdf_utils_weasy import generate_user_report_pdf_weasy

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_user)
    
    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_pass)
    
    async def test_email(self, db: Session, test_email: str) -> dict:
        """Odešle testovací email"""
        try:
            # Načti nastavení z databáze
            settings = db.query(EmailSettings).first()
            if not settings or not settings.is_enabled:
                return {"error": "Email služba není povolena"}
            
            if not settings.username or not settings.password:
                return {"error": "Email údaje nejsou kompletní"}
            
            # Vytvoř testovací email
            msg = MIMEMultipart()
            msg['From'] = settings.from_email or settings.username
            msg['To'] = test_email
            msg['Subject'] = "🍺 Test email - Beer Counter"
            
            body = "Testovací email z Beer Counter aplikace. Email služba funguje správně! 🍻"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # Odešli email
            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                start_tls=True,
                username=settings.username,
                password=settings.password,
            )
            
            return {"message": f"Test email úspěšně odeslán na {test_email}"}
            
        except Exception as e:
            return {"error": f"Chyba při odesílání: {str(e)}"}
    
    async def send_weekend_reports(self, db: Session) -> dict:
        """Rozešle PDF vyúčtování všem uživatelům s nenulovou spotřebou"""
        settings = db.query(EmailSettings).first()
        if not settings or not settings.is_enabled:
            return {"error": "Email služba není povolena", "count": 0}
        
        if not settings.username or not settings.password:
            return {"error": "Email údaje nejsou kompletní", "count": 0}
        
        sent_count = 0
        errors = []
        users = db.query(User).all()
        
        for user in users:
            user_counts = db.query(UserArticleCount).join(Article).filter(
                UserArticleCount.user_id == user.id,
                UserArticleCount.count > 0
            ).all()
            
            if not user_counts or not user.email:
                continue
                
            try:
                # Vygeneruj PDF
                total_amount = sum(count.count * count.article.price for count in user_counts)
                pdf_buffer = generate_user_report_pdf_weasy(user, user_counts, total_amount)
                
                # Vytvoř a odešli email
                await self._send_user_report(user, pdf_buffer, total_amount, settings)
                sent_count += 1
                
            except Exception as e:
                errors.append(f"{user.email}: {str(e)}")
        
        return {
            "message": f"Rozesláno {sent_count} vyúčtování",
            "count": sent_count,
            "errors": errors
        }
    
    async def _send_user_report(self, user: User, pdf_buffer, total_amount: float, settings):
        """Odešle vyúčtování jednomu uživateli"""
        msg = MIMEMultipart()
        msg['From'] = settings.from_email or settings.username
        msg['To'] = user.email
        msg['Subject'] = f"🍺 Víkendové vyúčtování - {user.username}"
        
        body = f"""Ahoj {user.username}!

Posíláme ti vyúčtování za víkend.
Celková částka: {total_amount} Kč

Děkujeme za návštěvu! 🍻
"""
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # Přilož PDF
        pdf_buffer.seek(0)
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="vyuctovani_{user.username}.pdf"'
        )
        msg.attach(attachment)
        
        # Odešli email
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=True,
            username=settings.username,
            password=settings.password,
        )

    async def send_single_user_report(self, db: Session, user: User) -> dict:
        """Odešle vyúčtování jednomu konkrétnímu uživateli"""
        try:
            settings = db.query(EmailSettings).first()
            if not settings or not settings.is_enabled:
                return {"error": "Email služba není povolena"}
            
            if not settings.username or not settings.password:
                return {"error": "Email údaje nejsou kompletní"}
            
            if not user.email:
                return {"error": f"Uživatel {user.username} nemá nastavený email"}
            
            # Získej počty uživatele
            user_counts = db.query(UserArticleCount).join(Article).filter(
                UserArticleCount.user_id == user.id,
                UserArticleCount.count > 0
            ).all()
            
            if not user_counts:
                return {"error": f"Uživatel {user.username} nemá žádné položky k vyúčtování"}
            
            # Vygeneruj PDF
            total_amount = sum(count.count * count.article.price for count in user_counts)
            pdf_buffer = generate_user_report_pdf_weasy(user, user_counts, total_amount)
            
            # Odešli email
            await self._send_user_report(user, pdf_buffer, total_amount, settings)
            
            return {"message": f"Vyúčtování úspěšně odesláno uživateli {user.username} na {user.email}"}
            
        except Exception as e:
            return {"error": f"Chyba při odesílání: {str(e)}"}

# Singleton instance
email_service = EmailService()

