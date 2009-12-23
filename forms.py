from django import forms

class CommentForm(forms.Form):
    author = forms.CharField(max_length=60)
    website = forms.URLField(required=False)
    comment = forms.CharField(widget=forms.Textarea, max_length=200000)
    
