from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration
import io
from datetime import datetime
import base64
from .utils import generate_payment_qr

def generate_user_report_pdf_weasy(user, user_counts, total_amount):
    """Generate PDF report using WeasyPrint with full emoji support"""
    
    # Seskup podle účtu pro QR kódy
    payment_groups = {}
    table_rows = ""
    
    for count in user_counts:
        if count.count > 0:
            total_price = count.count * count.article.price
            table_rows += f"""
            <tr>
                <td>{count.article.emoji} {count.article.name}</td>
                <td>{count.count}</td>
                <td>{count.article.price} Kč</td>
                <td>{total_price} Kč</td>
            </tr>
            """
            
            # Seskup podle účtu pro QR kódy
            account = count.article.payment_account or "123456789/0100"
            if account not in payment_groups:
                payment_groups[account] = {"total": 0, "items": []}
            payment_groups[account]["total"] += total_price
            payment_groups[account]["items"].append({
                "name": count.article.name,
                "emoji": count.article.emoji,
                "count": count.count
            })
    
    # QR kódy sekce
    qr_sections = ""
    for account, data in payment_groups.items():
        if data["total"] > 0:
            items_text = ", ".join([f"{item['count']}x {item['name']}" for item in data["items"]])
            message = f"{items_text} - {user.username}"
            qr_data_url = generate_payment_qr(data["total"], message, account)
            
            qr_sections += f"""
            <div class="qr-section">
                <h3>QR kód pro platbu - účet: {account}</h3>
                <div class="qr-container">
                    <img src="{qr_data_url}" alt="QR kód" class="qr-code">
                    <div class="qr-info">
                        <p><strong>Částka: {data['total']} Kč</strong></p>
                        <p>Účet: {account}</p>
                    </div>
                </div>
            </div>
            """
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Rozúčtování</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&family=Roboto:wght@400;700&display=swap');
            
            body {{
                font-family: 'Roboto', 'Noto Color Emoji', sans-serif;
                margin: 40px;
                line-height: 1.6;
            }}
            
            h1 {{
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }}
            
            .date {{
                text-align: center;
                margin-bottom: 30px;
                color: #666;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 30px;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: center;
            }}
            
            th {{
                background-color: #f5f5f5;
                font-weight: bold;
            }}
            
            .total-row {{
                background-color: #e8f4f8;
                font-weight: bold;
            }}
            
            .qr-section {{
                margin: 30px 0;
                page-break-inside: avoid;
            }}
            
            .qr-container {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            
            .qr-code {{
                width: 120px;
                height: 120px;
            }}
            
            .qr-info {{
                flex: 1;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 40px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <h1>🍺 Rozúčtování pro {user.username}</h1>
        
        <div class="date">
            Datum: {datetime.now().strftime('%d.%m.%Y %H:%M')}
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Položka</th>
                    <th>Počet</th>
                    <th>Cena za kus</th>
                    <th>Celkem</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
                <tr class="total-row">
                    <td colspan="3">CELKEM:</td>
                    <td>{total_amount} Kč</td>
                </tr>
            </tbody>
        </table>
        
        {qr_sections}
        
        <div class="footer">
            Děkujeme za návštěvu! 🍻
        </div>
    </body>
    </html>
    """
    
    # Generuj PDF
    font_config = FontConfiguration()
    html = HTML(string=html_content)
    pdf_bytes = html.write_pdf(font_config=font_config)
    
    return io.BytesIO(pdf_bytes)