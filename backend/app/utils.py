import qrcode
import io
import base64

def generate_qr_code(data: str) -> str:
    """Generate QR code and return as base64 data URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

def generate_payment_qr(amount: float, message: str, account: str) -> str:
    """Generate QR code for bank payment with account number"""
    # Formát pro české banky (SPAYD) - bez MSG
    payment_string = f"SPD*1.0*ACC:CZ{account}*AM:{amount:.2f}*CC:CZK*"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"






