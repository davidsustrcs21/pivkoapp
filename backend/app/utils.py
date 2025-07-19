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
    """Generate payment QR code for Czech banking - test both formats"""
    
    # Zkusíme formát podle vašeho fungujícího příkladu z AirBank
    # SPD*1.0*ACC:CZ7855000000001021238768*AM:1100.00*CC:CZK*X-URL:https://rb.cz
    qr_data = f"SPD*1.0*ACC:{account}*AM:{amount:.2f}*CC:CZK*X-URL:https://example.com"
    
    print(f"=== QR CODE DEBUG ===")
    print(f"Account: {account}")
    print(f"Amount: {amount:.2f}")
    print(f"Message: {message}")
    print(f"QR Data: {qr_data}")
    print(f"QR Data length: {len(qr_data)}")
    print("====================")
    
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"



