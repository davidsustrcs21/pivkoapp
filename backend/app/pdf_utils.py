from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from datetime import datetime
import base64
from .utils import generate_payment_qr

# Registrace fontu pro UTF-8 podporu
try:
    # Zkus různé možné cesty k DejaVu fontům
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/DejaVuSans.ttf'
    ]
    
    font_found = False
    for font_path in font_paths:
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', font_path.replace('.ttf', '-Bold.ttf')))
            DEFAULT_FONT = 'DejaVuSans'
            BOLD_FONT = 'DejaVuSans-Bold'
            font_found = True
            break
        except:
            continue
    
    if not font_found:
        raise Exception("DejaVu fonts not found")
        
except:
    # Fallback na standardní fonty
    DEFAULT_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'
    print("Warning: Using fallback fonts, Czech characters may not display correctly")

def generate_user_report_pdf(user, user_counts, total_amount):
    """Generate PDF report for user consumption with QR codes"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Styles s UTF-8 podporou
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        fontName=BOLD_FONT
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT
    )
    
    # Content
    story = []
    
    # Title
    title = Paragraph(f"🍺 Rozúčtování pro {user.username}", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Date
    date_text = f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    story.append(Paragraph(date_text, normal_style))
    story.append(Spacer(1, 20))
    
    # Table data
    data = [['Položka', 'Počet', 'Cena za kus', 'Celkem']]
    payment_groups = {}
    
    for count in user_counts:
        if count.count > 0:
            total_price = count.count * count.article.price
            data.append([
                f"{count.article.emoji} {count.article.name}",
                str(count.count),
                f"{count.article.price} Kč",
                f"{total_price} Kč"
            ])
            
            # Seskup podle účtu pro QR kódy
            account = count.article.payment_account or "123456789/0100"
            if account not in payment_groups:
                payment_groups[account] = {"total": 0, "items": []}
            payment_groups[account]["total"] += total_price
            payment_groups[account]["items"].append({
                "name": count.article.name,
                "count": count.count
            })
    
    # Add total row
    data.append(['', '', 'CELKEM:', f"{total_amount} Kč"])
    
    # Create table
    table = Table(data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
        ('FONTNAME', (0, 1), (-1, -1), DEFAULT_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), BOLD_FONT),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # QR kódy pro platbu
    for account, data in payment_groups.items():
        if data["total"] > 0:
            story.append(Paragraph(f"QR kód pro platbu - účet: {account}", 
                                 ParagraphStyle('QRTitle', parent=normal_style, fontSize=14, fontName=BOLD_FONT)))
            story.append(Spacer(1, 10))
            
            items_text = ", ".join([f"{item['count']}x {item['name']}" for item in data["items"]])
            message = f"{items_text} - {user.username}"
            
            # Generuj QR kód
            qr_data_url = generate_payment_qr(data["total"], message, account)
            qr_data = qr_data_url.split(',')[1]  # Odstraň "data:image/png;base64,"
            qr_bytes = base64.b64decode(qr_data)
            qr_buffer = io.BytesIO(qr_bytes)
            
            # Přidej QR obrázek
            qr_img = Image(qr_buffer, width=4*cm, height=4*cm)
            story.append(qr_img)
            story.append(Spacer(1, 10))
            
            story.append(Paragraph(f"Částka: {data['total']} Kč", normal_style))
            story.append(Spacer(1, 20))
    
    # Footer
    footer_text = "Děkujeme za návštěvu! 🍻"
    story.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_admin_summary_pdf(users_data, articles):
    """Generate PDF summary for admin"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        fontName=BOLD_FONT
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=DEFAULT_FONT
    )
    
    story = []
    
    # Title
    title = Paragraph("🍺 Celkový přehled spotřeby", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Date
    date_text = f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    story.append(Paragraph(date_text, normal_style))
    story.append(Spacer(1, 20))
    
    # Users table
    data = [['Uživatel'] + [f"{art.emoji} {art.name}" for art in articles] + ['Celkem']]
    
    for user_data in users_data:
        row = [user_data['username']]
        total = 0
        for article in articles:
            count = user_data.get(f'article_{article.id}', 0)
            row.append(str(count))
            total += count * article.price
        row.append(f"{total} Kč")
        data.append(row)
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
        ('FONTNAME', (0, 1), (-1, -1), DEFAULT_FONT),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer




