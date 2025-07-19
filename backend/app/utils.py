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
    """Generate payment QR code for Czech banking - correct SPAYD format"""
    # Ořežeme zprávu pokud je příliš dlouhá
    if len(message) > 60:
        message = message[:57] + "..."
    
    # Pokud účet není v IBAN formátu, použijeme ho přímo
    # SPAYD podporuje jak IBAN tak český formát
    if not account.startswith('CZ'):
        # Český formát účtu - použijeme přímo
        account_formatted = account
    else:
        # IBAN formát
        account_formatted = account
    
    # Správný formát podle vzoru
    qr_data = f"SPD*1.0*ACC:{account_formatted}*AM:{amount:.2f}*CC:CZK*MSG:{message}"
    
    print(f"=== QR CODE DEBUG ===")
    print(f"Original account: {account}")
    print(f"Formatted account: {account_formatted}")
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













