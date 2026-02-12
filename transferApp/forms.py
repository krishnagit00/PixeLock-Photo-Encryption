from django import forms

class SendForm(forms.Form):
    file = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'hidden-upload-input'}))
    text_content = forms.CharField(widget=forms.Textarea, required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    # Toggle in image 4 suggests option to use 6-digit code vs just a link
    use_6_digit_code = forms.BooleanField(initial=True, required=False)

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        text = cleaned_data.get("text_content")

        if not file and not text:
            raise forms.ValidationError("Please provide either a file or text content.")
        
        if file and file.size > 1 * 1024 * 1024 * 1024: # 1GB limit from image
             raise forms.ValidationError("File too large. Max size is 1GB.")
        return cleaned_data

class ReceiveForm(forms.Form):
    # Image 3: "Enter code or paste link..."
    code_or_link = forms.CharField(max_length=255, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
