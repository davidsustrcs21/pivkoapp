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
    from datetime import datetime
    
    # Rozlož číslo účtu na číslo a kód banky
    if '/' in account:
        account_number, bank_code = account.split('/')
    else:
        account_number = account
        bank_code = "0100"  # default
    
    # Doplň nuly do kódu banky na 4 cifry a čísla účtu na 10 cifer
    bank_code = bank_code.zfill(4)
    padded_account = account_number.zfill(10)
    
    # Aktuální datum
    today = datetime.now().strftime('%Y%m%d')
    
    # Použij 98 jako kontrolní číslice (standardní pro české účty)
    payment_string = f"SPD*1.0*ACC:CZ98{bank_code}0000{padded_account}*CC:CZK*DT:{today}*"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(payment_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"


































