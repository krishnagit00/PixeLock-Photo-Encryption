from django import forms

class LockerAccessForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control bg-black text-white border-secondary',
            'placeholder': 'you@example.com'
        })
    )
    pin = forms.CharField(
        max_length=6, 
        min_length=4,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-black text-white border-secondary',
            'placeholder': 'Set or Enter 4-6 digit PIN',
            'inputmode': 'numeric',
            'pattern': '[0-9]*'
        })
    )
 