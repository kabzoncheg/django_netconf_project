from django import forms


class UploadConfigForm(forms.Form):
    config_description = forms.CharField(label='Configuration description', max_length=200, required=False)
    config = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
