from django.db import models

class LockerUser(models.Model):
    email = models.EmailField(unique=True)
    # Store the PIN hash (securely), not the plain text PIN
    pin_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

class LockerFile(models.Model):
    user = models.ForeignKey(LockerUser, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='locker_files/%Y/%m/')
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    key = models.CharField(max_length=255, blank=True)