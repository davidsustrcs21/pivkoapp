from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import io
from datetime import datetime

def generate_user_report_pdf(user, user_counts, total_amount):
    """Generate PDF report for user consumption"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Content
    story = []
    
    # Title
    title = Paragraph(f"🍺 Rozúčtování pro {user.username}", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Date
    date_text = f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    story.append(Paragraph(date_text, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Table data
    data = [['Položka', 'Počet', 'Cena za kus', 'Celkem']]
    
    for count in user_counts:
        if count.count > 0:
            total_price = count.count * count.article.price
            data.append([
                f"{count.article.emoji} {count.article.name}",
                str(count.count),
                f"{count.article.price} Kč",
                f"{total_price} Kč"
            ])
    
    # Add total row
    data.append(['', '', 'CELKEM:', f"{total_amount} Kč"])
    
    # Create table
    table = Table(data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Footer
    footer_text = "Děkujeme za návštěvu! 🍻"
    story.append(Paragraph(footer_text, styles['Normal']))
    
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
        alignment=1
    )
    
    story = []
    
    # Title
    title = Paragraph("🍺 Celkový přehled spotřeby", title_style)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Date
    date_text = f"Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    story.append(Paragraph(date_text, styles['Normal']))
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
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer