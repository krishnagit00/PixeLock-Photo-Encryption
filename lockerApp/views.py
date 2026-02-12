from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from .forms import LockerAccessForm
from .models import LockerUser, LockerFile
from transferApp.utils import encrypt_file, generate_key
def locker_login_view(request):
    # If already logged in, go straight to dashboard
    if request.session.get('locker_user_id'):
        return redirect('lockerApp:dashboard')

    if request.method == 'POST':
        form = LockerAccessForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            pin = form.cleaned_data['pin']
            
            try:
                # SCENARIO 1: User Exists -> Check PIN
                user = LockerUser.objects.get(email=email)
                
                if check_password(pin, user.pin_hash):
                    # Correct PIN: Login
                    request.session['locker_user_id'] = user.id
                    return redirect('lockerApp:dashboard')
                else:
                    # Wrong PIN
                    form.add_error('pin', "Incorrect PIN for this locker.")
            
            except LockerUser.DoesNotExist:
                # SCENARIO 2: New User -> Create Account & PIN
                new_user = LockerUser.objects.create(
                    email=email,
                    pin_hash=make_password(pin) # Securely hash the PIN
                )
                request.session['locker_user_id'] = new_user.id
                return redirect('lockerApp:dashboard')

    else:
        form = LockerAccessForm()

    return render(request, 'locker.html', {'form': form})


def locker_dashboard_view(request):
    # Ensure user is logged in
    user_id = request.session.get('locker_user_id')
    if not user_id:
        return redirect('lockerApp:login')
    
    try:
        user = LockerUser.objects.get(id=user_id)
    except LockerUser.DoesNotExist:
        del request.session['locker_user_id']
        return redirect('lockerApp:login')

    # Handle Logout
    if request.method == 'POST' and 'logout' in request.POST:
        del request.session['locker_user_id']
        return redirect('lockerApp:login')

    # Handle File Upload
    if request.method == 'POST' and request.FILES.get('file'):
            uploaded_file = request.FILES['file']
            
            # 1. Generate Key
            key, _ = generate_key() 
            
            # 2. Encrypt
            encrypted_blob = encrypt_file(uploaded_file, key)
            
            # 3. THE FIX: Give the blob the original filename
            encrypted_blob.name = uploaded_file.name  
            
            # 4. Save
            LockerFile.objects.create(
                user=user,
                file=encrypted_blob,
                filename=uploaded_file.name,
                key=key.decode()
            )
            return redirect('lockerApp:dashboard')

    # Show Files
    files = user.files.all().order_by('-uploaded_at')
    
    context = {
        'user_email': user.email,
        'files': files
    }
    return render(request, 'locker.html', context)
#encrytion logic

from django.http import HttpResponse, Http404
from transferApp.utils import decrypt_file_data
import mimetypes

def download_locker_file(request, file_id):
    # 1. Security Check: Is user logged in?
    user_id = request.session.get('locker_user_id')
    if not user_id:
        return redirect('lockerApp:login')

    try:
        # 2. Get the file (and ensure it belongs to this user!)
        locker_file = LockerFile.objects.get(id=file_id, user_id=user_id)

        # 3. Read the encrypted data from disk
        with locker_file.file.open('rb') as f:
            encrypted_data = f.read()

        # 4. Decrypt using the stored key
        decrypted_data = decrypt_file_data(encrypted_data, locker_file.key.encode())

        # 5. Serve it as a download
        response = HttpResponse(decrypted_data, content_type=mimetypes.guess_type(locker_file.filename)[0])
        response['Content-Disposition'] = f'attachment; filename="{locker_file.filename}"'
        return response

    except LockerFile.DoesNotExist:
        raise Http404("File not found or access denied.")