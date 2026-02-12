import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def generate_key(password=None, salt=None):
    """Generates a Fernet key. If password is provided, derives key using PBKDF2."""
    if password:
        if not salt:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    else:
        return Fernet.generate_key(), None

def encrypt_file(file_handle, key):
    
    f = Fernet(key)
    file_data = file_handle.read()
    encrypted_data = f.encrypt(file_data)
    return ContentFile(encrypted_data)

def decrypt_file_data(encrypted_data, key):
   
    f = Fernet(key)
    return f.decrypt(encrypted_data)

def generate_qr_code(data):
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
