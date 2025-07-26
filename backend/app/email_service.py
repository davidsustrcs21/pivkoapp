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