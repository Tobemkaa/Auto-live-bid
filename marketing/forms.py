from django import forms


class ContactForm(forms.Form):
    name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={
        "placeholder": "Your name", "required": "required",
    }))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={
        "placeholder": "e.g. 0803 123 4567", "required": "required",
    }))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        "placeholder": "you@email.com", "required": "required",
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        "placeholder": "Tell us the make/model, a Copart link, or the bulk item you need...",
        "rows": 5, "required": "required",
    }))