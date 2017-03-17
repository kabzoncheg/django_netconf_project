from django import forms


class UploadConfigForm(forms.Form):
    config_description = forms.CharField(label='Configuration description', max_length=200, required=False,
                                         widget=forms.TextInput(attrs={'class': 'form_base'}))
    config = forms.FileField(label='', widget=forms.ClearableFileInput(attrs={'multiple': True, 'class': 'form_upload'}))
