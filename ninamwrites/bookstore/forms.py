from django import forms

class NewsletterForm(forms.Form):
    subject = forms.CharField(max_length=255, required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
