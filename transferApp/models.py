from django.db import models
import uuid
import random
import string
from django.utils import timezone
import datetime

def generate_6_digit_code():
    return ''.join(random.choices(string.digits, k=6))

def transfer_file_path(instance, filename):
    # Store files in a temporary subfolder
    return f'temp_transfers/{instance.unique_id}/{filename}'

class Transfer(models.Model):
    # The 6-digit retrieval code
    unique_code = models.CharField(max_length=6, default=generate_6_digit_code, unique=True, editable=False)
    # Internal UUID for robust lookup
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # The ENCRYPTED file
    encrypted_file = models.FileField(upload_to=transfer_file_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="Size in bytes")
    
    # Security
    is_password_protected = models.BooleanField(default=False)
    password_hash = models.CharField(max_length=128, blank=True, null=True)
    # Salt used if password protected
    encryption_salt = models.BinaryField(blank=True, null=True)
    # NOTE: In a stricter E2EE setup, we wouldn't store the key on server at all.
    # For this implementation, we store the key needed to decrypt, unless password protected.
    server_key = models.BinaryField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Default expiry: 24 hours
            self.expires_at = timezone.now() + datetime.timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Transfer {self.unique_code}"
