from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings
from django.utils import timezone
import os
import mimetypes
import uuid

from .forms import SendForm, ReceiveForm
from .models import Transfer
from .utils import generate_key, encrypt_file, decrypt_file_data, generate_qr_code

def send_view(request):
    # Matches Image 4 template
    if request.method == 'POST':
        form = SendForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data.get('file')
            password = form.cleaned_data.get('password')
            # text_content handling omitted for brevity, focusing on image encryption as requested

            if uploaded_file:
                # 1. Generate Encryption Key/Salt
                encryption_key, salt = generate_key(password if password else None)

                # 2. Encrypt the file
                encrypted_file_content = encrypt_file(uploaded_file, encryption_key)

                # 3. Create Transfer Object
                transfer = Transfer(
                    original_filename=uploaded_file.name,
                    file_size=uploaded_file.size,
                    is_password_protected=bool(password),
                    encryption_salt=salt,
                )

                if password:
                    transfer.password_hash = make_password(password)
                    # Key is derived from password on receipt, don't store it.
                else:
                    # No password, we must temporarily store the key to allow decryption
                    transfer.server_key = encryption_key
                
                # Save encrypted file to model
                transfer.encrypted_file.save(f"{uuid.uuid4()}.enc", encrypted_file_content)
                transfer.save()

                # Generate sharing links/QR
                download_link = request.build_absolute_uri(
                    reverse('transferApp:receive_direct', args=[transfer.unique_code])
                )
                qr_image_base64 = generate_qr_code(download_link)

                # Update session history (optional, based on Image 1)
                history = request.session.get('transfer_history', [])
                history.insert(0, {
                    'type': 'sent',
                    'filename': transfer.original_filename,
                    'size': transfer.file_size,
                    'date': timezone.now().isoformat()
                })
                request.session['transfer_history'] = history[:50] # Keep last 50

                context = {
                    'success': True,
                    'transfer': transfer,
                    'download_link': download_link,
                    'qr_image': qr_image_base64
                }
                # Use the same send template, but with success state data
                return render(request, 'send.html', context)

    else:
        form = SendForm()

    return render(request, 'send.html', {'form': form})


def receive_view(request):
    # Matches Image 3 template
    if request.method == 'POST':
        form = ReceiveForm(request.POST)
        if form.is_valid():
            code_input = form.cleaned_data.get('code_or_link')
            password_input = form.cleaned_data.get('password')
            
            # Extract 6-digit code if a full link was pasted
            code = code_input.split('/')[-1] if '/' in code_input else code_input

            try:
                transfer = Transfer.objects.get(unique_code=code)
            except Transfer.DoesNotExist:
                 form.add_error('code_or_link', "Invalid code.")
                 return render(request, 'receive.html', {'form': form})

            if transfer.is_expired:
                 form.add_error('code_or_link', "This transfer has expired.")
                 return render(request, 'receive.html', {'form': form})

            # Password Verification
            if transfer.is_password_protected:
                if not password_input:
                    # Re-render form asking for password
                    return render(request, 'receive.html', {'form': form, 'password_required': True})
                
                if not check_password(password_input, transfer.password_hash):
                    form.add_error('password', "Incorrect password.")
                    return render(request, 'receive.html', {'form': form, 'password_required': True})
                
                # Regenerate key from password
                decryption_key, _ = generate_key(password_input, transfer.encryption_salt)
            else:
                # Use stored server key
                decryption_key = transfer.server_key

            # Decrypt and serve
            try:
                with open(transfer.encrypted_file.path, 'rb') as f:
                    encrypted_data = f.read()
                
                decrypted_data = decrypt_file_data(encrypted_data, decryption_key)

                # Serve file
                content_type, _ = mimetypes.guess_type(transfer.original_filename)
                response = HttpResponse(decrypted_data, content_type=content_type or 'application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{transfer.original_filename}"'
                
                # Update history
                history = request.session.get('transfer_history', [])
                history.insert(0, {'type': 'received', 'filename': transfer.original_filename, 'size': transfer.file_size, 'date': timezone.now().isoformat()})
                request.session['transfer_history'] = history[:50]

                return response

            except Exception as e:
                # Handle decryption failure
                return HttpResponse("Error decrypting file. The transfer may be corrupted.", status=500)

    else:
        form = ReceiveForm()

    return render(request, 'receive.html', {'form': form})

# Helper view for direct links (e.g. from QR code)
def receive_direct_view(request, code):
    # Redirects to main receive page with code pre-filled
    # You might need to pass this via session or GET query parameter depending on your JS implementation in templates.
    # For simplicity here, we just render the receive template.
    form = ReceiveForm(initial={'code_or_link': code})
    return render(request, 'receive.html', {'form': form})

#this here is the code for rate limiting which will prevent a ip enter wrong pin mltiple times and then block that ip for some time

from django.core.cache import cache
from django.shortcuts import render, redirect

def receive_file(request):
    # 1. Get User IP
    user_ip = request.META.get('REMOTE_ADDR')
    
    # 2. Check if this IP is blocked
    if cache.get(f"block_{user_ip}"):
        return render(request, 'error.html', {'message': "Too many failed attempts. Try again in 15 minutes."})

    if request.method == 'POST':
        code = request.POST.get('code_or_link')
        
        try:
            # Try to find the file...
            transfer = Transfer.objects.get(unique_code=code)
            
            # SUCCESS: Clear any previous bad attempts
            cache.delete(f"attempts_{user_ip}")
            return render(request, 'download.html', {'transfer': transfer})
            
        except Transfer.DoesNotExist:
            # FAILURE: Increment attempt counter
            key = f"attempts_{user_ip}"
            attempts = cache.get(key, 0) + 1
            cache.set(key, attempts, 300) # Store for 5 minutes
            
            # If 5 fails, BLOCK them for 15 mins
            if attempts >= 3:
                cache.set(f"block_{user_ip}", True, 900) 
                
            return render(request, 'receive.html', {'error': "Invalid Code."})
            
    return render(request, 'receive.html')

#landing page
def landing_page(request):
    """Renders the main landing page."""
    return render(request, 'landing_page.html')